"""Tests for file cache persistence and retention behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from worksection_mcp.cache.file_cache import FileCache


@pytest.mark.asyncio
async def test_save_get_content_delete_and_stats(tmp_path):
    """Cache should persist files, expose content, and report stats."""
    cache = FileCache(cache_path=tmp_path / "cache", max_file_size_bytes=1024, retention_hours=24)
    try:
        await cache.save("file-1", b"hello world", filename="sample.txt")
        cached = await cache.get("file-1")
        assert cached is not None
        assert cached.mime_type == "text/plain"
        assert await cache.get_content("file-1") == b"hello world"

        stats = await cache.get_cache_stats()
        assert stats["file_count"] == 1
        assert stats["total_size_bytes"] == 11

        assert await cache.delete("file-1") is True
        assert await cache.get("file-1") is None
        assert await cache.delete("file-1") is False
    finally:
        await cache.close()


@pytest.mark.asyncio
async def test_save_rejects_files_larger_than_limit(tmp_path):
    """Cache should reject file content larger than configured max size."""
    cache = FileCache(cache_path=tmp_path / "cache", max_file_size_bytes=3, retention_hours=24)
    try:
        with pytest.raises(ValueError, match="exceeds limit"):
            await cache.save("big", b"1234", filename="big.bin")
    finally:
        await cache.close()


@pytest.mark.asyncio
async def test_invalid_image_is_downgraded_to_octet_stream(tmp_path):
    """Invalid image bytes should not be labeled as image mime type."""
    cache = FileCache(cache_path=tmp_path / "cache", max_file_size_bytes=1024, retention_hours=24)
    try:
        await cache.save("bad-image", b"not really png", filename="image.png")
        cached = await cache.get("bad-image")
        assert cached is not None
        assert cached.mime_type == "application/octet-stream"
    finally:
        await cache.close()


@pytest.mark.asyncio
async def test_missing_or_expired_cache_entries_are_cleaned_up(tmp_path):
    """Cache should remove metadata for missing and expired files."""
    cache = FileCache(cache_path=tmp_path / "cache", max_file_size_bytes=1024, retention_hours=1)
    try:
        # Missing file on disk should cause metadata cleanup in get()
        path = await cache.save("missing-file", b"abc", filename="a.txt")
        path.unlink()
        assert await cache.get("missing-file") is None

        # Expired row should be removed by get() and cleanup_expired()
        await cache.save("expired", b"xyz", filename="b.txt")
        db = await cache._get_db()
        old_timestamp = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        await db.execute(
            "UPDATE files SET cached_at = ? WHERE file_id = ?", (old_timestamp, "expired")
        )
        await db.commit()
        assert await cache.get("expired") is None

        await cache.save("cleanup-expired", b"123", filename="c.txt")
        await db.execute(
            "UPDATE files SET cached_at = ? WHERE file_id = ?",
            (old_timestamp, "cleanup-expired"),
        )
        await db.commit()
        assert await cache.cleanup_expired() == 1
        assert await cache.get("cleanup-expired") is None
    finally:
        await cache.close()
