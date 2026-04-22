"""Large MCP tool response offloading.

This module provides a central safety layer for MCP tool responses that are too
large to return through the protocol. Oversized responses are serialized to
local storage and replaced with compact metadata.
"""

from __future__ import annotations

import base64
import functools
import hashlib
import json
import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from worksection_mcp.mcp_protocols import ToolRegistrar

if TYPE_CHECKING:
    from worksection_mcp.config import Settings

logger = logging.getLogger(__name__)

LARGE_RESPONSE_TYPE = "large_tool_response"
OFFLOAD_HINT = (
    "The full response was stored because it exceeded the configured MCP response size limit."
)
VALID_SUFFIXES = (".json", ".txt", ".bin")
TEXT_MIME_TYPES = {
    ".json": "application/json",
    ".txt": "text/plain; charset=utf-8",
}
SUFFIX_MIME_TYPES = {
    **TEXT_MIME_TYPES,
    ".bin": "application/octet-stream",
}
RESPONSE_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
PAYLOAD_FILE_RE = re.compile(r"^ws_response_[0-9a-fA-F]{32}\.(json|txt|bin)$")
TMP_FILE_RE = re.compile(r"^ws_response_[0-9a-fA-F]{32}\.(json|txt|bin)\.tmp$")
TMP_RETENTION_SECONDS = 3600
RESOURCE_PREVIEW_BYTES = 1024
JSON_SERIALIZATION_ERRORS = (TypeError, ValueError)


def _trim_to_utf8_boundary(data: bytes) -> bytes:
    """Trim up to 3 trailing bytes to land on a complete UTF-8 character.

    A fixed-size byte read from a UTF-8 file may cut a multi-byte sequence in
    half. Trimming the partial sequence keeps decode() lossless and ensures
    the caller's next offset starts at a clean character boundary.
    Only called when more content follows, so the trimmed bytes are not lost.
    """
    for trim in range(min(3, len(data))):
        try:
            data[: len(data) - trim].decode("utf-8")
            return data[: len(data) - trim]
        except UnicodeDecodeError:
            continue
    return data  # underlying data is invalid UTF-8; leave errors="replace" to handle it


@dataclass(frozen=True)
class SerializedPayload:
    """Serialized tool response payload ready for size checks and storage."""

    content: bytes
    mime_type: str
    suffix: str


def serialize_tool_result(result: Any) -> SerializedPayload:
    """Serialize any supported tool result to bytes with a storage format."""
    if isinstance(result, bytes):
        return SerializedPayload(
            content=result,
            mime_type="application/octet-stream",
            suffix=".bin",
        )

    if isinstance(result, str):
        return SerializedPayload(
            content=result.encode("utf-8"),
            mime_type="text/plain; charset=utf-8",
            suffix=".txt",
        )

    try:
        content = json.dumps(result, default=str, ensure_ascii=False).encode("utf-8")
        return SerializedPayload(
            content=content,
            mime_type="application/json",
            suffix=".json",
        )
    except JSON_SERIALIZATION_ERRORS:
        content = repr(result).encode("utf-8", errors="replace")
        return SerializedPayload(
            content=content,
            mime_type="text/plain; charset=utf-8",
            suffix=".txt",
        )


class LargeResponseStore:
    """Store and retrieve oversized MCP tool responses."""

    def __init__(
        self,
        offload_dir: Path,
        threshold_bytes: int,
        retention_hours: int,
        max_files: int,
        include_file_path: bool,
        max_read_bytes: int,
    ) -> None:
        self.offload_dir = Path(offload_dir)
        self.threshold_bytes = threshold_bytes
        self.retention_hours = retention_hours
        self.max_files = max_files
        self.include_file_path = include_file_path
        self.max_read_bytes = max_read_bytes

    @classmethod
    def from_settings(cls, settings: Settings) -> LargeResponseStore:
        """Build a store from application settings."""
        return cls(
            offload_dir=settings.large_response_offload_path,
            threshold_bytes=settings.large_response_offload_threshold_bytes,
            retention_hours=settings.large_response_offload_retention_hours,
            max_files=settings.large_response_offload_max_files,
            include_file_path=settings.large_response_offload_include_file_path,
            max_read_bytes=settings.large_response_max_read_bytes,
        )

    def offload_if_needed(self, result: Any) -> Any:
        """Return result unchanged if small, otherwise offload and return metadata."""
        if self.threshold_bytes == 0:
            return result

        payload = serialize_tool_result(result)
        size_bytes = len(payload.content)
        if size_bytes <= self.threshold_bytes:
            return result

        try:
            self.offload_dir.mkdir(parents=True, exist_ok=True)
            response_id, final_path = self._write_atomic(payload)
            created_at = datetime.now(UTC).isoformat()
            metadata = self._metadata_for_path(
                response_id=response_id,
                path=final_path,
                content=payload.content,
                created_at=created_at,
            )
            metadata.update(
                {
                    "offloaded": True,
                    "type": LARGE_RESPONSE_TYPE,
                    "hint": OFFLOAD_HINT,
                }
            )
            return metadata
        except OSError:
            logger.exception("Could not offload oversized MCP response")
            return {
                "offload_failed": True,
                "type": LARGE_RESPONSE_TYPE,
                "size_bytes": size_bytes,
                "mime_type": payload.mime_type,
                "suffix": payload.suffix,
                "error": "Could not write large response to configured offload path.",
            }

    def cleanup(self) -> None:
        """Remove expired and excess offloaded response files."""
        try:
            self.offload_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.warning("Could not create large response offload directory", exc_info=True)
            return

        now = time.time()
        cutoff = now - (self.retention_hours * 3600)

        payload_files: list[Path] = []
        for path in self.offload_dir.iterdir():
            if path.is_file() and TMP_FILE_RE.fullmatch(path.name):
                self._delete_if_stale_tmp(path, now)
                continue

            if not path.is_file() or not PAYLOAD_FILE_RE.fullmatch(path.name):
                continue

            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                else:
                    payload_files.append(path)
            except OSError:
                logger.warning("Could not clean large response file %s", path, exc_info=True)

        payload_files = [path for path in payload_files if path.exists()]
        if len(payload_files) <= self.max_files:
            return

        payload_files.sort(key=lambda path: path.stat().st_mtime)
        for path in payload_files[: len(payload_files) - self.max_files]:
            try:
                path.unlink()
            except OSError:
                logger.warning(
                    "Could not remove excess large response file %s", path, exc_info=True
                )

    def get_payload_path(self, response_id: str) -> Path | None:
        """Return the stored payload path for an ID, if valid and present."""
        if not self._is_valid_response_id(response_id):
            return None

        for suffix in VALID_SUFFIXES:
            candidate = self.offload_dir / f"ws_response_{response_id}{suffix}"
            if candidate.exists() and candidate.is_file():
                return candidate

        return None

    def get_payload_metadata(self, response_id: str) -> dict[str, Any]:
        """Return metadata for an offloaded response."""
        if not self._is_valid_response_id(response_id):
            return {"error": "Invalid response_id format."}

        path = self.get_payload_path(response_id)
        if path is None:
            return {"error": "Offloaded response not found.", "response_id": response_id}

        return self._metadata_for_path(response_id=response_id, path=path)

    def read_text_slice(self, response_id: str, offset: int, max_bytes: int) -> dict[str, Any]:
        """Read a bounded UTF-8 text slice from an offloaded JSON/text response."""
        if offset < 0:
            return {"error": "offset must be greater than or equal to 0."}
        if max_bytes <= 0:
            return {"error": "max_bytes must be greater than 0."}
        if max_bytes > self.max_read_bytes:
            return {
                "error": "max_bytes exceeds configured large_response_max_read_bytes",
                "max_allowed_bytes": self.max_read_bytes,
            }
        if not self._is_valid_response_id(response_id):
            return {"error": "Invalid response_id format."}

        path = self.get_payload_path(response_id)
        if path is None:
            return {"error": "Offloaded response not found.", "response_id": response_id}

        mime_type = self._mime_type_for_path(path)
        if mime_type == "application/octet-stream":
            return {
                "error": "Offloaded response is binary. Text reads are not supported.",
                "mime_type": mime_type,
            }

        total_size = path.stat().st_size
        with path.open("rb") as f:
            f.seek(offset)
            raw = f.read(max_bytes)

        # Trim to the last complete UTF-8 character when more content follows.
        # The final chunk reads exactly what remains, so it needs no trimming.
        has_more_raw = offset + len(raw) < total_size
        chunk = _trim_to_utf8_boundary(raw) if has_more_raw else raw
        returned_bytes = len(chunk)
        return {
            "response_id": response_id,
            "offset": offset,
            "requested_bytes": max_bytes,
            "returned_bytes": returned_bytes,
            "content": chunk.decode("utf-8", errors="replace"),
            "has_more": offset + returned_bytes < total_size,
            "total_size_bytes": total_size,
        }

    def get_resource_preview(self, response_id: str) -> dict[str, Any]:
        """Return a small MCP resource-safe preview for an offloaded response."""
        metadata = self.get_payload_metadata(response_id)
        if "error" in metadata:
            return {
                "uri": f"worksection://offload/{response_id}",
                "mimeType": "application/json",
                "metadata": metadata,
            }

        path = self.get_payload_path(response_id)
        if path is None:
            return {
                "uri": f"worksection://offload/{response_id}",
                "mimeType": "application/json",
                "metadata": {"error": "Offloaded response not found.", "response_id": response_id},
            }

        mime_type = self._mime_type_for_path(path)
        with path.open("rb") as f:
            preview = f.read(RESOURCE_PREVIEW_BYTES)

        resource: dict[str, Any] = {
            "uri": f"worksection://offload/{response_id}",
            "mimeType": mime_type,
            "metadata": metadata,
        }

        if mime_type == "application/octet-stream":
            resource["preview_base64"] = base64.b64encode(preview).decode("ascii")
        else:
            resource["text"] = preview.decode("utf-8", errors="replace")

        return resource

    def _write_atomic(self, payload: SerializedPayload) -> tuple[str, Path]:
        response_id = uuid.uuid4().hex
        final_path = self.offload_dir / f"ws_response_{response_id}{payload.suffix}"
        tmp_path = final_path.with_suffix(f"{final_path.suffix}.tmp")

        try:
            tmp_path.write_bytes(payload.content)
            tmp_path.replace(final_path)
        except Exception:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                logger.warning("Could not remove failed large response temp file %s", tmp_path)
            raise

        return response_id, final_path

    def _metadata_for_path(
        self,
        response_id: str,
        path: Path,
        content: bytes | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        if content is None:
            content = path.read_bytes()

        stat = path.stat()
        if created_at is None:
            created_at = datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()

        metadata: dict[str, Any] = {
            "id": response_id,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "mime_type": self._mime_type_for_path(path),
            "suffix": path.suffix,
            "created_at": created_at,
            "resource_uri": f"worksection://offload/{response_id}",
        }
        if self.include_file_path:
            metadata["file_path"] = str(path.resolve())

        return metadata

    def _mime_type_for_path(self, path: Path) -> str:
        return SUFFIX_MIME_TYPES.get(path.suffix, "application/octet-stream")

    def _is_valid_response_id(self, response_id: str) -> bool:
        return bool(RESPONSE_ID_RE.fullmatch(response_id))

    def _delete_if_stale_tmp(self, path: Path, now: float) -> None:
        try:
            if now - path.stat().st_mtime > TMP_RETENTION_SECONDS:
                path.unlink()
        except OSError:
            logger.warning("Could not clean large response temp file %s", path, exc_info=True)


class LargePayloadToolRegistrar:
    """Tool registrar wrapper that offloads oversized tool responses."""

    def __init__(self, inner: ToolRegistrar, store: LargeResponseStore) -> None:
        self._inner = inner
        self._store = store

    def _wrap(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*fn_args: Any, **fn_kwargs: Any) -> Any:
            result = await func(*fn_args, **fn_kwargs)
            return self._store.offload_if_needed(result)

        return wrapper

    def tool(self, *args: Any, **kwargs: Any) -> Any:
        """Register a tool directly or return a wrapped registration decorator."""
        if args and callable(args[0]):
            func = cast(Callable[..., Awaitable[Any]], args[0])
            return self._inner.tool(self._wrap(func), *args[1:], **kwargs)

        inner_decorator = self._inner.tool(*args, **kwargs)

        def decorator(func: Callable[..., Awaitable[Any]]) -> Any:
            return inner_decorator(self._wrap(func))

        return decorator
