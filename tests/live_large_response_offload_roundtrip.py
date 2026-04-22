#!/usr/bin/env python3
"""
End-to-end test: large response handling round-trip.

Verifies the full cycle with a real Worksection API:
  1. Tool returning a large payload  → offload envelope returned
  2. get_offloaded_response_info     → metadata confirmed
  3. read_offloaded_response_text    → full content readable in chunks
  4. SHA-256 of reassembled content  → matches envelope (integrity check)

Usage:
    uv run python tests/live_large_response_offload_roundtrip.py
    uv run python tests/live_large_response_offload_roundtrip.py -v
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

from fastmcp import FastMCP

from worksection_mcp.auth import OAuth2Manager
from worksection_mcp.cache import FileCache
from worksection_mcp.client import WorksectionClient
from worksection_mcp.config import get_settings
from worksection_mcp.large_response import LargePayloadToolRegistrar, LargeResponseStore
from worksection_mcp.tools import register_all_tools
from worksection_mcp.tools.offload import register_offload_tools

# Low threshold so any real API response triggers offloading.
OFFLOAD_THRESHOLD = 1_000  # 1 KB

# Max bytes per read_offloaded_response_text call. Keep aligned with the
# project default so the live script validates production-like reads.
READ_CHUNK = 50_000

# Tools tried in order. First one that produces an offload envelope wins.
# get_task_tags returns ~100 KB with no required params — ideal trigger.
TRIGGER_CANDIDATES: list[tuple[str, dict[str, Any]]] = [
    ("get_task_tags", {}),
    ("get_all_tasks", {"status_filter": "active"}),
    ("get_projects", {}),
]


def out(msg: str = "") -> None:
    sys.stdout.write(f"{msg}\n")
    sys.stdout.flush()


def check(label: str, condition: bool, detail: str = "") -> bool:
    icon = "✅" if condition else "❌"
    line = f"  {icon} {label}"
    if detail:
        line += f"  ({detail})"
    out(line)
    return condition


async def _get_tool_fn(
    mcp: FastMCP[Any],
    name: str,
) -> Callable[..., Awaitable[Any]] | None:
    """Return the callable fn for a registered tool, or None."""
    for tool in await mcp.list_tools():
        if tool.name == name:
            fn = getattr(tool, "fn", None)
            if callable(fn):
                return cast(Callable[..., Awaitable[Any]], fn)
    return None


async def run(verbose: bool) -> bool:
    all_passed = True

    with tempfile.TemporaryDirectory(prefix="ws_offload_test_") as tmpdir:
        offload_dir = Path(tmpdir) / "offload"

        out("=" * 62)
        out("  LARGE RESPONSE OFFLOAD — INTEGRATION TEST")
        out("=" * 62)
        out(f"  Offload dir : {offload_dir}")
        out(f"  Threshold   : {OFFLOAD_THRESHOLD:,} bytes")
        out()

        # ── Auth & client setup ───────────────────────────────────
        settings = get_settings()
        oauth = OAuth2Manager(settings)
        client = WorksectionClient(oauth, settings)
        file_cache = FileCache(
            cache_path=settings.file_cache_path,
            max_file_size_bytes=settings.max_file_size_bytes,
            retention_hours=settings.file_cache_retention_hours,
        )

        out("Authenticating...")
        await oauth.ensure_authenticated()
        out("✓ Authenticated\n")

        # ── Wire offload layer ────────────────────────────────────
        store = LargeResponseStore(
            offload_dir=offload_dir,
            threshold_bytes=OFFLOAD_THRESHOLD,
            retention_hours=1,
            max_files=10,
            include_file_path=True,
            max_read_bytes=READ_CHUNK,
        )

        mcp: FastMCP[Any] = FastMCP("offload-test")
        registrar = LargePayloadToolRegistrar(mcp, store)
        register_all_tools(registrar, client, oauth, file_cache)
        register_offload_tools(mcp, store)  # raw mcp — not wrapped

        # ── STEP 1: trigger offloading ────────────────────────────
        out("─" * 62)
        out("  STEP 1 — Trigger offloading")
        out("─" * 62)

        envelope: dict[str, Any] | None = None
        trigger_tool: str | None = None

        for tool_name, params in TRIGGER_CANDIDATES:
            fn = await _get_tool_fn(mcp, tool_name)
            if fn is None:
                out(f"  ⊘ {tool_name} — not registered, skipping")
                continue

            param_str = json.dumps(params) if params else "no params"
            out(f"  Calling {tool_name} ({param_str})...")
            result = await fn(**params)

            if isinstance(result, dict) and result.get("offloaded") is True:
                envelope = result
                trigger_tool = tool_name
                out(f"  ✅ {tool_name} → offload envelope received")
                break

            inline_size = len(json.dumps(result, default=str))
            out(f"  ⊘ {tool_name} → returned inline ({inline_size:,} chars)")

        if envelope is None:
            out()
            out("  ❌ No trigger tool produced an offload envelope.")
            out("     All candidates returned responses below the threshold.")
            out(f"     Try lowering OFFLOAD_THRESHOLD (currently {OFFLOAD_THRESHOLD:,} bytes)")
            out("     or add a trigger candidate that returns more data.")
            await client.close()
            await file_cache.close()
            return False

        if verbose:
            out()
            out("  Envelope:")
            for k, v in envelope.items():
                out(f"    {k}: {v}")

        response_id: str = envelope["id"]
        expected_sha256: str = envelope["sha256"]
        expected_size: int = envelope["size_bytes"]
        out()

        # ── STEP 2: validate envelope fields ──────────────────────
        out("─" * 62)
        out("  STEP 2 — Validate offload envelope")
        out("─" * 62)

        for field in (
            "offloaded",
            "type",
            "id",
            "size_bytes",
            "sha256",
            "mime_type",
            "suffix",
            "resource_uri",
            "created_at",
            "hint",
            "file_path",
        ):
            all_passed &= check(f"has '{field}'", field in envelope)

        all_passed &= check("offloaded is True", envelope.get("offloaded") is True)
        all_passed &= check(
            "type is 'large_tool_response'",
            envelope.get("type") == "large_tool_response",
        )
        all_passed &= check(
            "resource_uri starts with worksection://offload/",
            str(envelope.get("resource_uri", "")).startswith("worksection://offload/"),
        )
        file_path = Path(envelope.get("file_path", ""))
        file_on_disk = await asyncio.to_thread(file_path.is_file)
        all_passed &= check(
            "file_path exists on disk",
            file_on_disk,
            file_path.name,
        )
        all_passed &= check(
            "size_bytes > threshold",
            expected_size > OFFLOAD_THRESHOLD,
            f"{expected_size:,} bytes",
        )
        out()

        # ── STEP 3: get_offloaded_response_info ───────────────────
        out("─" * 62)
        out("  STEP 3 — get_offloaded_response_info")
        out("─" * 62)

        info_fn = await _get_tool_fn(mcp, "get_offloaded_response_info")
        if info_fn is None:
            out("  ❌ get_offloaded_response_info not registered")
            await client.close()
            await file_cache.close()
            return False

        info = await info_fn(response_id=response_id)

        if verbose:
            out()
            out("  Info:")
            for k, v in info.items():
                out(f"    {k}: {v}")
            out()

        all_passed &= check("no error field", "error" not in info, info.get("error", ""))
        all_passed &= check("id matches", info.get("id") == response_id)
        all_passed &= check(
            "size_bytes matches envelope",
            info.get("size_bytes") == expected_size,
            f"{info.get('size_bytes'):,} bytes",
        )
        all_passed &= check("sha256 matches envelope", info.get("sha256") == expected_sha256)
        out()

        # ── STEP 4: chunked read-back + integrity check ───────────
        out("─" * 62)
        out("  STEP 4 — read_offloaded_response_text (chunked)")
        out("─" * 62)

        read_fn = await _get_tool_fn(mcp, "read_offloaded_response_text")
        if read_fn is None:
            out("  ❌ read_offloaded_response_text not registered")
            await client.close()
            await file_cache.close()
            return False

        mime_type = envelope.get("mime_type", "")
        if mime_type == "application/octet-stream":
            out("  ⊘ Binary payload — text read not applicable for this MIME type")
        else:
            chunks: list[str] = []
            offset = 0
            call_count = 0
            read_error = False

            while True:
                call_count += 1
                result = await read_fn(
                    response_id=response_id,
                    offset=offset,
                    max_bytes=READ_CHUNK,
                )

                if "error" in result:
                    all_passed &= check(f"chunk {call_count} read OK", False, result["error"])
                    read_error = True
                    break

                chunk_text: str = result.get("content", "")
                returned: int = result.get("returned_bytes", 0)
                has_more: bool = result.get("has_more", False)
                chunks.append(chunk_text)
                offset += returned

                if verbose:
                    out(
                        f"  chunk {call_count}: "
                        f"offset={offset - returned:,}  "
                        f"returned={returned:,}  "
                        f"has_more={has_more}"
                    )

                if not has_more:
                    break

            if not read_error:
                reassembled = "".join(chunks)
                reassembled_bytes = reassembled.encode("utf-8")

                all_passed &= check(
                    f"read in {call_count} chunk(s)",
                    call_count >= 1,
                    f"{len(reassembled_bytes):,} bytes total",
                )
                all_passed &= check(
                    "reassembled size matches stored",
                    len(reassembled_bytes) == expected_size,
                    f"{len(reassembled_bytes):,} == {expected_size:,}",
                )
                actual_sha256 = hashlib.sha256(reassembled_bytes).hexdigest()
                all_passed &= check(
                    "sha256 roundtrip",
                    actual_sha256 == expected_sha256,
                    actual_sha256[:16] + "...",
                )

                if mime_type == "application/json":
                    try:
                        json.loads(reassembled)
                        all_passed &= check("content is valid JSON", True)
                    except json.JSONDecodeError as exc:
                        all_passed &= check("content is valid JSON", False, str(exc))

        out()

        # ── Summary ───────────────────────────────────────────────
        out("=" * 62)
        if all_passed:
            out("  ✅ ALL CHECKS PASSED")
        else:
            out("  ❌ SOME CHECKS FAILED")
        out(f"  Trigger tool  : {trigger_tool}")
        out(f"  Payload size  : {expected_size:,} bytes")
        out(f"  MIME type     : {envelope.get('mime_type')}")
        out(f"  Response ID   : {response_id}")
        out("=" * 62)

        await client.close()
        await file_cache.close()

    return all_passed


def main() -> None:
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    success = asyncio.run(run(verbose=verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
