"""Tests for file MCP resources."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.helpers import FakeMCP
from worksection_mcp.cache.file_cache import CachedFile
from worksection_mcp.resources.files import register_file_resources


@pytest.mark.asyncio
async def test_get_file_resource_uses_cache_for_text_file(tmp_path):
    """Resource should return decoded text content for cached text files."""
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello from cache", encoding="utf-8")

    cache_hit = CachedFile(
        file_id="f1",
        path=file_path,
        mime_type="text/plain",
        size_bytes=file_path.stat().st_size,
        cached_at=datetime.now(UTC),
    )
    fake_cache = SimpleNamespace(
        get=AsyncMock(return_value=cache_hit),
        save=AsyncMock(),
        get_cache_stats=AsyncMock(return_value={}),
    )
    fake_client = SimpleNamespace(
        download_file=AsyncMock(),
        get_task=AsyncMock(),
        get_comments=AsyncMock(),
    )

    mcp = FakeMCP()
    register_file_resources(mcp, fake_client, fake_cache)

    result = await mcp.resources["get_file_resource"]("f1")
    assert result["uri"] == "worksection://file/f1"
    assert result["mimeType"] == "text/plain"
    assert result["text"] == "hello from cache"
    fake_client.download_file.assert_not_called()


@pytest.mark.asyncio
async def test_get_file_resource_downloads_and_returns_binary_blob(tmp_path):
    """Resource should download/cache on miss and return base64 blob for binaries."""
    file_path = tmp_path / "image.bin"
    file_bytes = b"\x89PNG\r\n\x1a\n..."
    file_path.write_bytes(file_bytes)

    cached_after_save = CachedFile(
        file_id="f2",
        path=file_path,
        mime_type="image/png",
        size_bytes=len(file_bytes),
        cached_at=datetime.now(UTC),
    )
    fake_cache = SimpleNamespace(
        get=AsyncMock(side_effect=[None, cached_after_save]),
        save=AsyncMock(),
        get_cache_stats=AsyncMock(return_value={}),
    )
    fake_client = SimpleNamespace(
        download_file=AsyncMock(return_value=file_bytes),
        get_task=AsyncMock(),
        get_comments=AsyncMock(),
    )

    mcp = FakeMCP()
    register_file_resources(mcp, fake_client, fake_cache)

    result = await mcp.resources["get_file_resource"]("f2")
    assert result["mimeType"] == "image/png"
    assert result["blob"] == base64.b64encode(file_bytes).decode("utf-8")
    fake_cache.save.assert_awaited_once_with("f2", file_bytes)


@pytest.mark.asyncio
async def test_get_task_full_context_aggregates_attachments_and_images():
    """Task context resource should aggregate task/comment attachments and image summary."""
    task_response = {"status": "ok", "data": {"id": "t1", "name": "Task 1"}}
    task_files_response = {
        "status": "ok",
        "data": {"files": [{"id": "f1", "name": "spec.pdf"}, {"id": "f2", "name": "shot.png"}]},
    }
    comments_response = {
        "status": "ok",
        "data": [
            {
                "id": "c1",
                "text": "Please review",
                "files": [{"id": "f3", "name": "wireframe.jpg"}],
            }
        ],
    }

    fake_cache = SimpleNamespace(get=AsyncMock(), save=AsyncMock(), get_cache_stats=AsyncMock())
    fake_client = SimpleNamespace(
        download_file=AsyncMock(),
        get_task=AsyncMock(side_effect=[task_response, task_files_response]),
        get_comments=AsyncMock(return_value=comments_response),
    )

    mcp = FakeMCP()
    register_file_resources(mcp, fake_client, fake_cache)

    result = await mcp.resources["get_task_full_context"]("t1")
    summary = result["data"]["summary"]
    assert summary["comment_count"] == 1
    assert summary["attachment_count"] == 3
    assert summary["image_count"] == 2


@pytest.mark.asyncio
async def test_get_cache_stats_resource_passthrough():
    """Cache stats resource should wrap file cache stats payload in MCP response shape."""
    stats = {"file_count": 3, "total_size_bytes": 1024}
    fake_cache = SimpleNamespace(
        get=AsyncMock(),
        save=AsyncMock(),
        get_cache_stats=AsyncMock(return_value=stats),
    )
    fake_client = SimpleNamespace(
        download_file=AsyncMock(), get_task=AsyncMock(), get_comments=AsyncMock()
    )

    mcp = FakeMCP()
    register_file_resources(mcp, fake_client, fake_cache)

    result = await mcp.resources["get_cache_stats"]()
    assert result["uri"] == "worksection://cache/stats"
    assert result["data"] == stats
