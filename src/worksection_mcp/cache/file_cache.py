"""File caching system for downloaded attachments."""

import asyncio
import hashlib
import logging
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

import aiosqlite
from PIL import Image

logger = logging.getLogger(__name__)


class CachedFile(NamedTuple):
    """Metadata for a cached file."""

    file_id: str
    path: Path
    mime_type: str
    size_bytes: int
    cached_at: datetime


class FileCache:
    """File cache with SQLite metadata storage."""

    DB_NAME = "cache_metadata.db"

    def __init__(
        self,
        cache_path: Path,
        max_file_size_bytes: int = 10 * 1024 * 1024,
        retention_hours: int = 24,
    ):
        """Initialize file cache.

        Args:
            cache_path: Directory for cached files
            max_file_size_bytes: Maximum file size to cache
            retention_hours: Hours to keep cached files
        """
        self.cache_path = cache_path
        self.max_file_size_bytes = max_file_size_bytes
        self.retention_hours = retention_hours
        self._db_path = cache_path / self.DB_NAME
        self._db: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

        # Ensure cache directory exists
        self.cache_path.mkdir(parents=True, exist_ok=True)

    async def _get_db(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._db is None:
            self._db = await aiosqlite.connect(self._db_path)
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    mime_type TEXT,
                    size_bytes INTEGER,
                    cached_at TEXT NOT NULL
                )
            """)
            await self._db.commit()
        return self._db

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    def _get_cache_path(self, file_id: str, extension: str = "") -> Path:
        """Generate cache file path for a file ID."""
        # Use hash of file_id to distribute files
        hash_prefix = hashlib.sha256(file_id.encode()).hexdigest()[:4]
        subdir = self.cache_path / hash_prefix
        subdir.mkdir(exist_ok=True)
        return subdir / f"{file_id}{extension}"

    async def save(
        self,
        file_id: str,
        content: bytes,
        filename: str | None = None,
    ) -> Path:
        """Save file content to cache.

        Args:
            file_id: Unique file identifier
            content: File content as bytes
            filename: Original filename (for extension detection)

        Returns:
            Path to cached file

        Raises:
            ValueError: If file exceeds size limit
        """
        if len(content) > self.max_file_size_bytes:
            raise ValueError(
                f"File size ({len(content)} bytes) exceeds limit ({self.max_file_size_bytes} bytes)"
            )

        async with self._lock:
            # Determine extension
            extension = ""
            if filename:
                extension = Path(filename).suffix

            # Detect mime type
            mime_type = mimetypes.guess_type(filename or "")[0] or "application/octet-stream"

            # If it's an image, verify it
            if mime_type.startswith("image/"):
                try:
                    # Verify it's a valid image
                    import io

                    img = Image.open(io.BytesIO(content))
                    img.verify()
                except Exception as e:
                    logger.warning(f"Invalid image file {file_id}: {e}")
                    mime_type = "application/octet-stream"

            # Save file
            cache_path = self._get_cache_path(file_id, extension)
            cache_path.write_bytes(content)

            # Update database
            db = await self._get_db()
            now = datetime.now(UTC).isoformat()
            await db.execute(
                """
                INSERT OR REPLACE INTO files (file_id, path, mime_type, size_bytes, cached_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_id, str(cache_path), mime_type, len(content), now),
            )
            await db.commit()

            logger.debug(f"Cached file {file_id} at {cache_path}")
            return cache_path

    async def get(self, file_id: str) -> CachedFile | None:
        """Get cached file metadata.

        Args:
            file_id: File ID to look up

        Returns:
            CachedFile if found and valid, None otherwise
        """
        db = await self._get_db()
        async with db.execute(
            "SELECT file_id, path, mime_type, size_bytes, cached_at FROM files WHERE file_id = ?",
            (file_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        file_id, path_str, mime_type, size_bytes, cached_at_str = row
        path = Path(path_str)

        # Check if file still exists
        if not await asyncio.to_thread(path.exists):
            await self.delete(file_id)
            return None

        # Check if file is expired
        cached_at = datetime.fromisoformat(cached_at_str)
        age_hours = (datetime.now(UTC) - cached_at).total_seconds() / 3600
        if age_hours > self.retention_hours:
            await self.delete(file_id)
            return None

        return CachedFile(
            file_id=file_id,
            path=path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            cached_at=cached_at,
        )

    async def get_content(self, file_id: str) -> bytes | None:
        """Get cached file content.

        Args:
            file_id: File ID to look up

        Returns:
            File content as bytes, or None if not cached
        """
        cached = await self.get(file_id)
        if cached and await asyncio.to_thread(cached.path.exists):
            return await asyncio.to_thread(cached.path.read_bytes)
        return None

    async def delete(self, file_id: str) -> bool:
        """Delete a cached file.

        Args:
            file_id: File ID to delete

        Returns:
            True if file was deleted
        """
        async with self._lock:
            db = await self._get_db()

            # Get path first
            async with db.execute("SELECT path FROM files WHERE file_id = ?", (file_id,)) as cursor:
                row = await cursor.fetchone()

            if row:
                path = Path(row[0])
                if await asyncio.to_thread(path.exists):
                    await asyncio.to_thread(path.unlink)

                await db.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
                await db.commit()
                logger.debug(f"Deleted cached file {file_id}")
                return True

            return False

    async def cleanup_expired(self) -> int:
        """Remove expired files from cache.

        Returns:
            Number of files removed
        """
        db = await self._get_db()
        cutoff = datetime.now(UTC).timestamp() - (self.retention_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=UTC).isoformat()

        # Get expired files
        async with db.execute(
            "SELECT file_id, path FROM files WHERE cached_at < ?",
            (cutoff_iso,),
        ) as cursor:
            expired = await cursor.fetchall()

        # Delete files
        count = 0
        for _file_id, path_str in expired:
            path = Path(path_str)
            if await asyncio.to_thread(path.exists):
                await asyncio.to_thread(path.unlink)
            count += 1

        # Remove from database
        if expired:
            await db.execute("DELETE FROM files WHERE cached_at < ?", (cutoff_iso,))
            await db.commit()

        if count > 0:
            logger.info(f"Cleaned up {count} expired cached files")

        return count

    async def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Cache statistics including file count, total size, etc.
        """
        db = await self._get_db()
        async with db.execute("SELECT COUNT(*), SUM(size_bytes) FROM files") as cursor:
            row = await cursor.fetchone()

        file_count = row[0] or 0
        total_size = row[1] or 0

        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_path": str(self.cache_path),
            "max_file_size_mb": self.max_file_size_bytes / (1024 * 1024),
            "retention_hours": self.retention_hours,
        }
