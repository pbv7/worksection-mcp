"""Tests for Worksection API client behavior."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from tests.helpers import build_settings
from worksection_mcp.client.api import WorksectionAPIError, WorksectionClient


@dataclass
class DummyLimiter:
    """Rate limiter stub used to avoid timing-dependent tests."""

    success_calls: int = 0
    rate_limit_calls: int = 0
    last_retry_after: float | None = None

    async def __aenter__(self) -> DummyLimiter:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def record_success(self) -> None:
        self.success_calls += 1

    def record_rate_limit(self, retry_after: float | None = None) -> None:
        self.rate_limit_calls += 1
        self.last_retry_after = retry_after


@pytest.fixture
def client(tmp_path):
    """Create client with mocked oauth manager and test settings."""
    settings = build_settings(tmp_path)
    oauth: Any = SimpleNamespace(
        get_valid_token=AsyncMock(return_value="test-token"),
        close=AsyncMock(),
    )
    return WorksectionClient(oauth=oauth, settings=settings)


@pytest.mark.asyncio
async def test_make_request_get_success(client):
    """GET request should include auth/action params and parse JSON."""
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(
        return_value=httpx.Response(200, json={"status": "ok", "data": [1]})
    )
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    data = await client._make_request("get_projects", params={"filter": "active"})

    assert data["data"] == [1]
    assert limiter.success_calls == 1
    http_client.get.assert_awaited_once()
    _, kwargs = http_client.get.await_args
    assert kwargs["params"] == {"action": "get_projects", "filter": "active"}
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_make_request_post_success(client):
    """POST branch should be used for non-GET method."""
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.post = AsyncMock(return_value=httpx.Response(200, json={"status": "ok"}))
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    await client._make_request("me", method="POST")

    assert limiter.success_calls == 1
    http_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_make_request_handles_rate_limit(client):
    """HTTP 429 should raise WorksectionAPIError and record backoff input."""
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(429, headers={"Retry-After": "2"}))
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="Rate limit exceeded") as exc_info:
        await client._make_request("get_projects")

    assert exc_info.value.status_code == 429
    assert limiter.rate_limit_calls == 1
    assert limiter.last_retry_after == 2.0


@pytest.mark.asyncio
async def test_make_request_handles_non_200(client):
    """Non-200 responses should raise WorksectionAPIError with status code."""
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(500, text="server error"))
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="API request failed"):
        await client._make_request("get_projects")


@pytest.mark.asyncio
async def test_make_request_handles_api_error_payload(client):
    """API error payload in a 200 response should still raise."""
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(
        return_value=httpx.Response(
            200,
            json={"error": "invalid_scope", "error_description": "scope mismatch"},
        )
    )
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="scope mismatch"):
        await client._make_request("get_projects")


@pytest.mark.asyncio
async def test_make_request_dns_connect_error(client):
    """DNS-like connect errors should return a tailored troubleshooting message."""
    request = httpx.Request("GET", client.settings.api_base_url)
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(
        side_effect=httpx.ConnectError("nodename nor servname provided", request=request)
    )
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="DNS resolution failed"):
        await client._make_request("get_projects")


@pytest.mark.asyncio
async def test_make_request_generic_connect_error(client):
    """Other connect errors should return generic connection guidance."""
    request = httpx.Request("GET", client.settings.api_base_url)
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(side_effect=httpx.ConnectError("connection reset", request=request))
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="Connection error"):
        await client._make_request("get_projects")


@pytest.mark.asyncio
async def test_make_request_request_error(client):
    """Request errors should include request context."""
    request = httpx.Request("GET", client.settings.api_base_url)
    limiter = DummyLimiter()
    http_client = AsyncMock()
    http_client.get = AsyncMock(side_effect=httpx.RequestError("timeout", request=request))
    client.rate_limiter = limiter
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="Request failed"):
        await client._make_request("get_projects")


@pytest.mark.asyncio
async def test_response_normalization_for_list_endpoints(client):
    """List endpoints should normalize missing data arrays to empty lists."""
    client._make_request = AsyncMock(return_value={"status": "ok"})  # type: ignore[method-assign]

    projects = await client.get_projects()
    tasks = await client.get_all_tasks()
    scoped_tasks = await client.get_tasks(project_id="p1")
    users = await client.get_users()

    assert projects["data"] == []
    assert tasks["data"] == []
    assert scoped_tasks["data"] == []
    assert users["data"] == []


@pytest.mark.asyncio
async def test_get_user_found_and_not_found(client):
    """get_user should search users list and return deterministic not-found payload."""
    client.get_users = AsyncMock(
        return_value={
            "status": "ok",
            "data": [
                {"id": "1", "name": "First"},
                {"id": "2", "name": "Second"},
            ],
        }
    )

    found = await client.get_user("2")
    missing = await client.get_user("99")

    assert found == {"status": "ok", "data": {"id": "2", "name": "Second"}}
    assert missing["status"] == "error"
    assert "99" in missing["message"]


@pytest.mark.asyncio
async def test_get_costs_param_transformation(client):
    """get_costs should transform dates and booleans to API-compliant params."""
    client._make_request = AsyncMock(return_value={"status": "ok"})  # type: ignore[method-assign]

    await client.get_costs(
        project_id="p1",
        task_id="t1",
        user_id="u1",
        date_start="2024-01-15",
        date_end="31.01.2024",
        is_timer=True,
    )

    client._make_request.assert_awaited_once_with(
        "get_costs",
        {
            "id_project": "p1",
            "id_task": "t1",
            "id_user": "u1",
            "datestart": "15.01.2024",
            "dateend": "31.01.2024",
            "is_timer": "1",
        },
    )


@pytest.mark.asyncio
async def test_search_tasks_and_events_params(client):
    """Search/events APIs should build request params from optional inputs."""
    client._make_request = AsyncMock(return_value={"status": "ok"})  # type: ignore[method-assign]

    await client.search_tasks(
        search_query="name has 'Bug'",
        project_id="p1",
        task_id="t1",
        email_user_from="author@example.com",
        email_user_to="assignee@example.com",
        status="active",
        extra="text",
    )
    await client.get_events(project_id="p1", period="7d")

    assert client._make_request.await_args_list[0].args == (
        "search_tasks",
        {
            "filter": "name has 'Bug'",
            "id_project": "p1",
            "id_task": "t1",
            "email_user_from": "author@example.com",
            "email_user_to": "assignee@example.com",
            "status": "active",
            "extra": "text",
        },
    )
    assert client._make_request.await_args_list[1].args == (
        "get_events",
        {"id_project": "p1", "period": "7d"},
    )


@pytest.mark.asyncio
async def test_download_file_success_and_failure(client):
    """download_file should return bytes on 200 and raise on error status."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    ok_http_client = AsyncMock()
    ok_http_client.get = AsyncMock(return_value=httpx.Response(200, content=b"abc"))
    client._get_http_client = AsyncMock(return_value=ok_http_client)  # type: ignore[method-assign]
    data = await client.download_file("file-1")
    assert data == b"abc"
    assert limiter.success_calls == 1

    bad_http_client = AsyncMock()
    bad_http_client.get = AsyncMock(return_value=httpx.Response(404, text="not found"))
    client._get_http_client = AsyncMock(return_value=bad_http_client)  # type: ignore[method-assign]
    with pytest.raises(WorksectionAPIError, match="File download failed"):
        await client.download_file("file-1")


@pytest.mark.asyncio
async def test_close_closes_http_client_and_oauth(client):
    """close should close both HTTP client and oauth manager."""
    fake_http_client = SimpleNamespace(is_closed=False, aclose=AsyncMock())
    client._http_client = fake_http_client  # type: ignore[assignment]

    await client.close()

    fake_http_client.aclose.assert_awaited_once()
    assert client._http_client is None
    client.oauth.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_http_client_creation_reuse_and_recreate_closed(client, monkeypatch):
    """HTTP client should be created once, reused, and recreated if closed."""
    created = []

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.is_closed = False
            created.append(self)

        async def aclose(self):
            self.is_closed = True

    monkeypatch.setattr("worksection_mcp.client.api.httpx.AsyncClient", FakeAsyncClient)

    first = await client._get_http_client()
    second = await client._get_http_client()
    assert first is second
    assert len(created) == 1
    assert first.kwargs["follow_redirects"] is True
    assert first.kwargs["timeout"] == 30.0

    first.is_closed = True
    third = await client._get_http_client()
    assert third is not first
    assert len(created) == 2


@pytest.mark.asyncio
async def test_project_and_task_wrappers_forward_optional_params(client):
    """Project/task wrappers should forward optional params and action names."""
    client._make_request = AsyncMock(return_value={"status": "ok", "data": []})  # type: ignore[method-assign]

    await client.get_projects(status_filter="active", extra="users")
    await client.get_project("p1", extra="text")
    await client.get_project_groups()
    await client.get_all_tasks(status_filter="done", extra="relations")
    await client.get_tasks(project_id="p2", status_filter="active", extra="files")
    await client.get_task("t1", extra="comments")
    await client.get_comments("t1", extra="files")

    assert client._make_request.await_args_list[0].args == (
        "get_projects",
        {"filter": "active", "extra": "users"},
    )
    assert client._make_request.await_args_list[1].args == (
        "get_project",
        {"id_project": "p1", "extra": "text"},
    )
    assert client._make_request.await_args_list[2].args == ("get_project_groups",)
    assert client._make_request.await_args_list[3].args == (
        "get_all_tasks",
        {"filter": "done", "extra": "relations"},
    )
    assert client._make_request.await_args_list[4].args == (
        "get_tasks",
        {"id_project": "p2", "filter": "active", "extra": "files"},
    )
    assert client._make_request.await_args_list[5].args == (
        "get_task",
        {"id_task": "t1", "extra": "comments"},
    )
    assert client._make_request.await_args_list[6].args == (
        "get_comments",
        {"id_task": "t1", "extra": "files"},
    )


@pytest.mark.asyncio
async def test_time_user_and_tag_wrappers_forward_params(client):
    """Costs/user/tag wrappers should build expected request params."""
    client._make_request = AsyncMock(return_value={"status": "ok", "data": []})  # type: ignore[method-assign]

    await client.get_costs_total(project_id="p1", date_start="2024-02-01", date_end="2024-02-03")
    await client.get_users(status_filter="active")
    await client.me()
    await client.get_user_groups()
    await client.get_contacts()
    await client.get_contact_groups()

    await client.get_task_tags(group="main", tag_type="label", access="public")
    await client.get_task_tag_groups(tag_type="status", access="private")
    await client.get_task_tag_groups()  # Empty filters should pass None payload
    await client.get_project_tags(group="main", tag_type="label", access="public")
    await client.get_project_tags()  # Empty filters should pass None payload
    await client.get_project_tag_groups(tag_type="status", access="private")
    await client.get_project_tag_groups()  # Empty filters should pass None payload

    assert client._make_request.await_args_list[0].args == (
        "get_costs_total",
        {"id_project": "p1", "datestart": "01.02.2024", "dateend": "03.02.2024"},
    )
    assert client._make_request.await_args_list[1].args == ("get_users", {"filter": "active"})
    assert client._make_request.await_args_list[2].args == ("me",)
    assert client._make_request.await_args_list[3].args == ("get_user_groups",)
    assert client._make_request.await_args_list[4].args == ("get_contacts",)
    assert client._make_request.await_args_list[5].args == ("get_contact_groups",)
    assert client._make_request.await_args_list[6].args == (
        "get_task_tags",
        {"group": "main", "type": "label", "access": "public"},
    )
    assert client._make_request.await_args_list[7].args == (
        "get_task_tag_groups",
        {"type": "status", "access": "private"},
    )
    assert client._make_request.await_args_list[8].args == ("get_task_tag_groups", None)
    assert client._make_request.await_args_list[9].args == (
        "get_project_tags",
        {"group": "main", "type": "label", "access": "public"},
    )
    assert client._make_request.await_args_list[10].args == ("get_project_tags", None)
    assert client._make_request.await_args_list[11].args == (
        "get_project_tag_groups",
        {"type": "status", "access": "private"},
    )
    assert client._make_request.await_args_list[12].args == ("get_project_tag_groups", None)


@pytest.mark.asyncio
async def test_timer_methods(client):
    """Timer methods should call POST with correct action names."""
    client._make_request = AsyncMock(return_value={"status": "ok", "data": []})  # type: ignore[method-assign]

    await client.get_timers()
    await client.get_my_timer()

    assert client._make_request.await_args_list[0].args == ("get_timers",)
    assert client._make_request.await_args_list[0].kwargs == {"method": "POST"}
    assert client._make_request.await_args_list[1].args == ("get_my_timer",)
    assert client._make_request.await_args_list[1].kwargs == {"method": "POST"}


@pytest.mark.asyncio
async def test_download_file_detects_api_error_json(client):
    """download_file should raise WorksectionAPIError when API returns error JSON."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    error_json = b'{"status":"error","msg":"File not found"}'
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=error_json))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="File not found"):
        await client.download_file("file-1")


@pytest.mark.asyncio
async def test_download_file_detects_api_error_with_whitespace(client):
    """download_file should handle leading whitespace in error JSON."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    error_json = b'  {"status":"error","message":"Access denied"}'
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=error_json))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    with pytest.raises(WorksectionAPIError, match="Access denied"):
        await client.download_file("file-1")


@pytest.mark.asyncio
async def test_download_file_passes_valid_small_json(client):
    """download_file should return valid small JSON files unchanged."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    valid_json = b'{"status":"ok","data":[]}'
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=valid_json))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    result = await client.download_file("file-1")
    assert result == valid_json


@pytest.mark.asyncio
async def test_download_file_passes_binary_content(client):
    """download_file should return binary content unchanged."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    binary = b"\x89PNG\r\n\x1a\nimagedata"
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=binary))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    result = await client.download_file("file-1")
    assert result == binary


@pytest.mark.asyncio
async def test_download_file_passes_large_json(client):
    """download_file should skip JSON parsing for payloads > 8KB."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    # Large JSON payload that happens to have status=error
    large_json = b'{"status":"error","msg":"big"}' + b"x" * 9000
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=large_json))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    result = await client.download_file("file-1")
    assert result == large_json


@pytest.mark.asyncio
async def test_download_file_no_msg_field_returns_bytes(client):
    """download_file should return bytes when status=error but no msg/message field."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    error_json = b'{"status":"error","data":[]}'
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=error_json))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    result = await client.download_file("file-1")
    assert result == error_json


@pytest.mark.asyncio
async def test_download_file_empty_msg_returns_bytes(client):
    """download_file should return bytes when msg is empty string."""
    limiter = DummyLimiter()
    client.rate_limiter = limiter

    error_json = b'{"status":"error","msg":""}'
    http_client = AsyncMock()
    http_client.get = AsyncMock(return_value=httpx.Response(200, content=error_json))
    client._get_http_client = AsyncMock(return_value=http_client)  # type: ignore[method-assign]

    result = await client.download_file("file-1")
    assert result == error_json


@pytest.mark.asyncio
async def test_get_events_only_sends_period_and_project(client):
    """get_events should only send period and id_project params to the API."""
    client._make_request = AsyncMock(return_value={"status": "ok", "data": []})  # type: ignore[method-assign]

    await client.get_events(project_id="p1", period="7d")

    client._make_request.assert_awaited_once_with(
        "get_events",
        {"id_project": "p1", "period": "7d"},
    )
