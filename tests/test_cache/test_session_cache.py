"""Tests for in-memory session cache."""

import asyncio

import pytest

from worksection_mcp.cache.session_cache import SessionCache


@pytest.mark.asyncio
async def test_set_and_get():
    """Cache should store and retrieve values."""
    cache = SessionCache()
    await cache.set("key1", {"data": [1, 2, 3]})
    result = await cache.get("key1")
    assert result == {"data": [1, 2, 3]}


@pytest.mark.asyncio
async def test_get_missing_key():
    """Cache should return None for missing keys."""
    cache = SessionCache()
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_ttl_expiry():
    """Cache entries should expire after TTL."""
    cache = SessionCache(default_ttl=0.05)
    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"
    await asyncio.sleep(0.1)
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_custom_ttl():
    """Custom TTL should override default."""
    cache = SessionCache(default_ttl=10.0)
    await cache.set("key1", "value1", ttl=0.05)
    assert await cache.get("key1") == "value1"
    await asyncio.sleep(0.1)
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_lru_eviction():
    """Cache should evict LRU entries when over max_entries."""
    cache = SessionCache(max_entries=3)
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)
    # Access 'a' to make it recently used
    await cache.get("a")
    # Add 'd' — should evict 'b' (least recently accessed)
    await cache.set("d", 4)
    assert cache.size <= 3
    assert await cache.get("a") is not None  # kept (recently accessed)
    assert await cache.get("d") is not None  # kept (just added)


@pytest.mark.asyncio
async def test_invalidate_by_pattern():
    """invalidate should remove entries matching pattern."""
    cache = SessionCache()
    await cache.set("get_tasks:p1", "data1")
    await cache.set("get_tasks:p2", "data2")
    await cache.set("get_users:", "data3")
    removed = await cache.invalidate("get_tasks")
    assert removed == 2
    assert await cache.get("get_tasks:p1") is None
    assert await cache.get("get_users:") == "data3"


@pytest.mark.asyncio
async def test_clear():
    """clear should remove all entries."""
    cache = SessionCache()
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.clear()
    assert cache.size == 0
    assert await cache.get("a") is None


@pytest.mark.asyncio
async def test_size_property():
    """size should reflect current entry count."""
    cache = SessionCache()
    assert cache.size == 0
    await cache.set("a", 1)
    assert cache.size == 1
    await cache.set("b", 2)
    assert cache.size == 2
