"""Tests for large response offloading."""

from __future__ import annotations

import inspect
import os
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

import pytest
from fastmcp import FastMCP

from tests.helpers import FakeMCP, build_settings
from worksection_mcp.large_response import (
    LargePayloadToolRegistrar,
    LargeResponseStore,
    serialize_tool_result,
)
from worksection_mcp.resources.offload import register_large_response_resources
from worksection_mcp.tools.offload import register_offload_tools


def make_store(
    tmp_path: Path,
    *,
    threshold_bytes: int = 100,
    include_file_path: bool = True,
    max_files: int = 100,
    retention_hours: int = 24,
    max_read_bytes: int = 50_000,
) -> LargeResponseStore:
    return LargeResponseStore(
        offload_dir=tmp_path / "offload",
        threshold_bytes=threshold_bytes,
        retention_hours=retention_hours,
        max_files=max_files,
        include_file_path=include_file_path,
        max_read_bytes=max_read_bytes,
    )


async def get_fastmcp_tool_fn(
    mcp: FastMCP[Any],
    name: str,
) -> Callable[..., Awaitable[Any]]:
    """Return a callable registered FastMCP tool by name."""
    for tool in await mcp.list_tools():
        if tool.name == name:
            fn = getattr(tool, "fn", None)
            if callable(fn):
                return cast(Callable[..., Awaitable[Any]], fn)
    raise AssertionError(f"FastMCP tool not registered: {name}")


def test_small_dict_returns_unchanged(tmp_path):
    store = make_store(tmp_path, threshold_bytes=10_000)
    result = {"ok": True}

    assert store.offload_if_needed(result) is result
    assert not store.offload_dir.exists()


@pytest.mark.parametrize(
    ("result", "suffix", "mime_type"),
    [
        ({"data": "x" * 200}, ".json", "application/json"),
        ([{"data": "x" * 200}], ".json", "application/json"),
        ("x" * 200, ".txt", "text/plain; charset=utf-8"),
        (b"x" * 200, ".bin", "application/octet-stream"),
    ],
)
def test_large_payloads_are_offloaded(tmp_path, result, suffix, mime_type):
    store = make_store(tmp_path, threshold_bytes=50)

    metadata = store.offload_if_needed(result)

    assert metadata["offloaded"] is True
    assert metadata["type"] == "large_tool_response"
    assert metadata["suffix"] == suffix
    assert metadata["mime_type"] == mime_type
    assert metadata["size_bytes"] > 50
    assert metadata["resource_uri"] == f"worksection://offload/{metadata['id']}"
    assert "created_at" in metadata
    assert "sha256" in metadata
    assert Path(metadata["file_path"]).exists()


def test_include_file_path_can_be_disabled(tmp_path):
    store = make_store(tmp_path, threshold_bytes=50, include_file_path=False)

    metadata = store.offload_if_needed({"data": "x" * 200})

    assert metadata["offloaded"] is True
    assert "file_path" not in metadata


def test_threshold_zero_disables_offload(tmp_path):
    store = make_store(tmp_path, threshold_bytes=0)
    result = {"data": "x" * 200}

    assert store.offload_if_needed(result) is result
    assert not store.offload_dir.exists()


def test_unsupported_object_falls_back_to_text():
    class BadString:
        def __str__(self) -> str:
            raise ValueError("no string")

    payload = serialize_tool_result({"bad": BadString()})

    assert payload.suffix == ".txt"
    assert payload.mime_type == "text/plain; charset=utf-8"
    assert b"BadString" in payload.content


def test_write_failure_returns_compact_failure(tmp_path, monkeypatch):
    store = make_store(tmp_path, threshold_bytes=50)

    def fail_write(_payload):
        raise OSError("denied")

    monkeypatch.setattr(store, "_write_atomic", fail_write)

    metadata = store.offload_if_needed({"data": "x" * 200})

    assert metadata == {
        "offload_failed": True,
        "type": "large_tool_response",
        "size_bytes": metadata["size_bytes"],
        "mime_type": "application/json",
        "suffix": ".json",
        "error": "Could not write large response to configured offload path.",
    }
    assert "data" not in metadata


def test_cleanup_deletes_old_files_enforces_count_and_ignores_unowned(tmp_path):
    store = make_store(tmp_path, threshold_bytes=50, retention_hours=1, max_files=1)
    store.offload_dir.mkdir(parents=True)

    old_owned = store.offload_dir / ("ws_response_" + "a" * 32 + ".json")
    keep_newer = store.offload_dir / ("ws_response_" + "b" * 32 + ".json")
    delete_oldest_excess = store.offload_dir / ("ws_response_" + "c" * 32 + ".txt")
    ignored = store.offload_dir / "someone_else.json"
    stale_tmp = store.offload_dir / ("ws_response_" + "d" * 32 + ".json.tmp")
    fresh_tmp = store.offload_dir / ("ws_response_" + "e" * 32 + ".json.tmp")

    for path in (old_owned, keep_newer, delete_oldest_excess, ignored, stale_tmp, fresh_tmp):
        path.write_text("x")

    now = time.time()
    os.utime(old_owned, (now - 7200, now - 7200))
    os.utime(delete_oldest_excess, (now - 1800, now - 1800))
    os.utime(keep_newer, (now, now))
    os.utime(stale_tmp, (now - 7200, now - 7200))
    os.utime(fresh_tmp, (now, now))

    store.cleanup()

    assert not old_owned.exists()
    assert not delete_oldest_excess.exists()
    assert not stale_tmp.exists()
    assert keep_newer.exists()
    assert ignored.exists()
    assert fresh_tmp.exists()


def test_cleanup_if_due_runs_during_offload_for_long_running_servers(tmp_path):
    store = make_store(tmp_path, threshold_bytes=5, retention_hours=1, max_files=10)
    store.offload_dir.mkdir(parents=True)
    stale = store.offload_dir / ("ws_response_" + "a" * 32 + ".json")
    stale.write_text("old")
    old_time = time.time() - 7200
    os.utime(stale, (old_time, old_time))

    metadata = store.offload_if_needed("x" * 20)

    assert metadata["offloaded"] is True
    assert not stale.exists()
    assert store._last_cleanup_at > 0


@pytest.mark.asyncio
async def test_registrar_preserves_signature_and_wraps_result(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=50)
    registrar = LargePayloadToolRegistrar(fake, store)

    @registrar.tool()
    async def sample_tool(project_id: str, limit: int = 10) -> dict:
        return {"project_id": project_id, "limit": limit, "data": "x" * 200}

    registered = fake.tools["sample_tool"]
    assert inspect.signature(registered) == inspect.signature(sample_tool)

    result = await registered("p1")
    assert result["offloaded"] is True


@pytest.mark.asyncio
async def test_registrar_supports_all_registration_forms(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=10_000)
    registrar = LargePayloadToolRegistrar(fake, store)

    async def direct() -> dict:
        return {"ok": "direct"}

    async def direct_named() -> dict:
        return {"ok": "direct_named"}

    registrar.tool(direct)
    registrar.tool(direct_named, name="custom_direct")

    @registrar.tool()
    async def factory() -> dict:
        return {"ok": "factory"}

    @registrar.tool(name="custom_factory")
    async def factory_named() -> dict:
        return {"ok": "factory_named"}

    assert set(fake.tools) == {"direct", "custom_direct", "factory", "custom_factory"}
    assert await fake.tools["direct"]() == {"ok": "direct"}
    assert await fake.tools["custom_direct"]() == {"ok": "direct_named"}
    assert await fake.tools["factory"]() == {"ok": "factory"}
    assert await fake.tools["custom_factory"]() == {"ok": "factory_named"}


@pytest.mark.asyncio
async def test_registrar_direct_registration_forms_work_with_fastmcp(tmp_path):
    mcp: FastMCP[Any] = FastMCP("large-response-registration-test")
    store = make_store(tmp_path, threshold_bytes=10_000)
    registrar = LargePayloadToolRegistrar(mcp, store)

    async def direct() -> dict:
        return {"ok": "direct"}

    async def direct_named() -> dict:
        return {"ok": "direct_named"}

    registrar.tool(direct)
    registrar.tool(direct_named, name="custom_direct")

    direct_fn = await get_fastmcp_tool_fn(mcp, "direct")
    direct_named_fn = await get_fastmcp_tool_fn(mcp, "custom_direct")

    assert await direct_fn() == {"ok": "direct"}
    assert await direct_named_fn() == {"ok": "direct_named"}


@pytest.mark.asyncio
async def test_offload_tools_read_text_validation_and_slicing(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=5, max_read_bytes=10)
    register_offload_tools(fake, store)

    metadata = store.offload_if_needed("hello world")
    response_id = metadata["id"]

    assert await fake.tools["read_offloaded_response_text"](response_id, offset=-1) == {
        "error": "offset must be greater than or equal to 0."
    }
    assert await fake.tools["read_offloaded_response_text"](response_id, max_bytes=0) == {
        "error": "max_bytes must be greater than 0."
    }
    assert await fake.tools["read_offloaded_response_text"](response_id, max_bytes=3) == {
        "error": "max_bytes must be at least 4 to preserve UTF-8 boundaries.",
        "min_allowed_bytes": 4,
    }
    assert await fake.tools["read_offloaded_response_text"](response_id, max_bytes=11) == {
        "error": "max_bytes exceeds configured large_response_max_read_bytes",
        "max_allowed_bytes": 10,
    }
    assert await fake.tools["read_offloaded_response_text"]("not-valid", max_bytes=5) == {
        "error": "Invalid response_id format."
    }

    result = await fake.tools["read_offloaded_response_text"](response_id, max_bytes=5)
    assert result["content"] == "hello"
    assert result["returned_bytes"] == 5
    assert result["has_more"] is True

    info = await fake.tools["get_offloaded_response_info"](response_id)
    assert info["id"] == response_id
    assert info["size_bytes"] == len("hello world")


@pytest.mark.asyncio
async def test_offload_tool_default_read_size_matches_safe_limit(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=5, max_read_bytes=8)
    register_offload_tools(fake, store)

    metadata = store.offload_if_needed("x" * 20)
    result = await fake.tools["read_offloaded_response_text"](metadata["id"])

    assert result["requested_bytes"] == 8
    assert result["returned_bytes"] == 8
    assert result["has_more"] is True


def test_read_text_slice_trims_to_utf8_boundary(tmp_path):
    store = make_store(tmp_path, threshold_bytes=5, max_read_bytes=10)
    # "日" = 3 bytes (e6 97 a5), "本" = 3 bytes (e6 9c ac) — total 6 bytes stored.
    text = "日本"
    metadata = store.offload_if_needed(text)
    response_id = metadata["id"]

    # Read 4 bytes: would normally split "日" (3 bytes) + first byte of "本".
    # Trimming should return only "日" (3 bytes) so the decode is lossless.
    result = store.read_text_slice(response_id, offset=0, max_bytes=4)
    assert result["content"] == "日"
    assert result["returned_bytes"] == 3
    assert result["has_more"] is True

    # Next read from byte 3 gets the remaining "本" exactly.
    result = store.read_text_slice(response_id, offset=3, max_bytes=4)
    assert result["content"] == "本"
    assert result["returned_bytes"] == 3
    assert result["has_more"] is False


def test_read_text_slice_trims_four_byte_utf8_boundary(tmp_path):
    store = make_store(tmp_path, threshold_bytes=5, max_read_bytes=10)
    text = "a🙂b"
    metadata = store.offload_if_needed(text)
    response_id = metadata["id"]

    result = store.read_text_slice(response_id, offset=0, max_bytes=4)
    assert result["content"] == "a"
    assert result["returned_bytes"] == 1
    assert result["has_more"] is True

    result = store.read_text_slice(response_id, offset=1, max_bytes=4)
    assert result["content"] == "🙂"
    assert result["returned_bytes"] == 4
    assert result["has_more"] is True


@pytest.mark.asyncio
async def test_offload_tools_reject_binary_reads(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=5)
    register_offload_tools(fake, store)

    metadata = store.offload_if_needed(b"x" * 20)

    result = await fake.tools["read_offloaded_response_text"](metadata["id"])

    assert result == {
        "error": "Offloaded response is binary. Text reads are not supported.",
        "mime_type": "application/octet-stream",
    }


@pytest.mark.asyncio
async def test_offload_tools_registered_on_raw_mcp_are_not_recursively_wrapped(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=5)
    register_offload_tools(fake, store)

    metadata = store.offload_if_needed("x" * 100)
    result = await fake.tools["read_offloaded_response_text"](metadata["id"])

    assert "offloaded" not in result
    assert result["content"] == "x" * 100


@pytest.mark.asyncio
async def test_offload_resource_returns_preview_not_full_payload(tmp_path):
    fake = FakeMCP()
    store = make_store(tmp_path, threshold_bytes=5)
    register_large_response_resources(fake, store)

    metadata = store.offload_if_needed("x" * 2000)
    result = await fake.resources["get_offloaded_response"](metadata["id"])

    assert result["uri"] == f"worksection://offload/{metadata['id']}"
    assert result["mimeType"] == "text/plain; charset=utf-8"
    assert len(result["text"]) == 1024
    assert result["metadata"]["id"] == metadata["id"]


def test_resource_preview_for_binary_payload_returns_base64_preview(tmp_path):
    store = make_store(tmp_path, threshold_bytes=5)
    payload = b"\x00\xffbinary-data" * 200
    metadata = store.offload_if_needed(payload)

    result = store.get_resource_preview(metadata["id"])

    assert result["uri"] == f"worksection://offload/{metadata['id']}"
    assert result["mimeType"] == "application/octet-stream"
    assert result["metadata"]["id"] == metadata["id"]
    assert "text" not in result
    assert "blob" not in result
    assert result["preview_base64"]


def test_get_payload_metadata_streams_existing_file_hash(tmp_path, monkeypatch):
    store = make_store(tmp_path, threshold_bytes=5)
    metadata = store.offload_if_needed("x" * 20)
    response_id = metadata["id"]

    def fail_read_bytes(self):
        raise AssertionError(f"read_bytes should not be called for metadata: {self}")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    info = store.get_payload_metadata(response_id)

    assert info["id"] == response_id
    assert info["size_bytes"] == metadata["size_bytes"]
    assert info["sha256"] == metadata["sha256"]


def test_from_settings_uses_large_response_config(tmp_path):
    settings = build_settings(
        tmp_path,
        large_response_offload_path=tmp_path / "custom-offload",
        large_response_offload_threshold_bytes=123,
        large_response_offload_retention_hours=2,
        large_response_offload_max_files=3,
        large_response_offload_include_file_path=False,
        large_response_max_read_bytes=456,
    )

    store = LargeResponseStore.from_settings(settings)

    assert store.offload_dir == tmp_path / "custom-offload"
    assert store.threshold_bytes == 123
    assert store.retention_hours == 2
    assert store.max_files == 3
    assert store.include_file_path is False
    assert store.max_read_bytes == 456


def test_settings_reject_too_small_large_response_max_read_bytes(tmp_path):
    with pytest.raises(ValueError, match="large_response_max_read_bytes"):
        build_settings(tmp_path, large_response_max_read_bytes=3)


def test_default_large_response_settings_use_client_safe_limits(tmp_path):
    settings = build_settings(tmp_path)

    assert settings.large_response_offload_threshold_bytes == 50_000
    assert settings.large_response_max_read_bytes == 50_000

    store = LargeResponseStore.from_settings(settings)

    assert store.threshold_bytes == 50_000
    assert store.max_read_bytes == 50_000
