"""Tests for API client caching, new endpoints, and response normalization."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from tests.helpers import build_settings
from worksection_mcp.client.api import WorksectionClient


@pytest.fixture
def client(tmp_path):
    """Create client with mocked oauth manager and test settings."""
    settings = build_settings(tmp_path)
    oauth: Any = SimpleNamespace(
        get_valid_token=AsyncMock(return_value="test-token"),
        close=AsyncMock(),
    )
    return WorksectionClient(oauth=oauth, settings=settings)


class DummyLimiter:
    """Rate limiter stub."""

    success_calls: int = 0
    rate_limit_calls: int = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def record_success(self):
        self.success_calls += 1

    def record_rate_limit(self, retry_after=None):
        self.rate_limit_calls += 1
        self.last_retry_after = retry_after


def _setup_client_with_json(client, json_data):
    """Wire up a client to return a specific JSON response."""
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, json=json_data))
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)
    return http_client


# ---------------------------------------------------------------------------
# Session cache integration
# ---------------------------------------------------------------------------


class TestRequestCaching:
    """Verify that use_cache=True causes cache reads and writes."""

    @pytest.mark.asyncio
    async def test_cache_hit_avoids_http_call(self, client):
        """A cached response should be returned without making an HTTP request."""
        await client.cache.set("get_projects:frozenset()", {"status": "ok", "data": [{"id": "p1"}]})

        http_client = AsyncMock()
        client._get_http_client = AsyncMock(return_value=http_client)

        data = await client._make_request("get_projects", use_cache=True)
        assert data["data"] == [{"id": "p1"}]
        http_client.get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_miss_stores_response(self, client):
        """On cache miss, the HTTP response should be stored for subsequent calls."""
        _setup_client_with_json(client, {"status": "ok", "data": []})

        await client._make_request("get_users", use_cache=True)

        cached = await client.cache.get("get_users:frozenset()")
        assert cached is not None
        assert cached["status"] == "ok"


# ---------------------------------------------------------------------------
# New client method delegation
# ---------------------------------------------------------------------------


class TestNewClientMethods:
    """Verify get_files and get_webhooks delegate to _make_request correctly."""

    @pytest.mark.asyncio
    async def test_get_files_with_project_and_task(self, client):
        """get_files should forward both project_id and task_id as params."""
        client._make_request = AsyncMock(return_value={"status": "ok", "data": []})

        await client.get_files(project_id="p1", task_id="t1")

        client._make_request.assert_awaited_once_with(
            "get_files", {"id_project": "p1", "id_task": "t1"}
        )

    @pytest.mark.asyncio
    async def test_get_files_project_only(self, client):
        """get_files with only project_id should omit task param."""
        client._make_request = AsyncMock(return_value={"status": "ok", "data": []})

        await client.get_files(project_id="p1")

        client._make_request.assert_awaited_once_with("get_files", {"id_project": "p1"})

    @pytest.mark.asyncio
    async def test_get_webhooks_passes_no_params(self, client):
        """get_webhooks should call _make_request with just the action name."""
        client._make_request = AsyncMock(return_value={"status": "ok", "data": []})

        await client.get_webhooks()

        client._make_request.assert_awaited_once_with("get_webhooks")

    @pytest.mark.asyncio
    async def test_get_contact_groups_passes_no_params(self, client):
        """get_contact_groups should call _make_request with just the action name."""
        client._make_request = AsyncMock(return_value={"status": "ok", "data": []})

        await client.get_contact_groups()

        client._make_request.assert_awaited_once_with("get_contact_groups")


# ---------------------------------------------------------------------------
# Response normalization on "data" key
# ---------------------------------------------------------------------------


class TestResponseNormalization:
    """The API sometimes omits the `data` key on success.  List endpoints
    must normalize this to an empty list so callers never get KeyError."""

    @pytest.mark.asyncio
    async def test_get_all_tasks_normalizes_missing_data(self, client):
        """get_all_tasks should inject data=[] when API returns status:ok without data."""
        client._make_request = AsyncMock(return_value={"status": "ok"})

        result = await client.get_all_tasks()

        assert result["data"] == []

    @pytest.mark.asyncio
    async def test_get_tasks_normalizes_missing_data(self, client):
        """get_tasks should inject data=[] when API omits it."""
        client._make_request = AsyncMock(return_value={"status": "ok"})

        result = await client.get_tasks(project_id="p1")

        assert result["data"] == []

    @pytest.mark.asyncio
    async def test_get_users_normalizes_missing_data(self, client):
        """get_users should inject data=[] when API omits it."""
        client._make_request = AsyncMock(return_value={"status": "ok"})

        result = await client.get_users()

        assert result["data"] == []
