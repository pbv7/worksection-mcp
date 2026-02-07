"""Tests for tool-level edge cases: search_tasks fallback, project_files validation, tag errors."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tests.helpers import FakeMCP
from worksection_mcp.client.api import WorksectionAPIError
from worksection_mcp.tools.files import register_file_tools
from worksection_mcp.tools.system import register_system_tools
from worksection_mcp.tools.tags import register_tag_tools
from worksection_mcp.tools.tasks import register_task_tools
from worksection_mcp.tools.timers import register_timer_tools


def _make_client(**overrides: Any) -> Any:
    defaults: dict[str, Any] = {
        "get_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task": AsyncMock(return_value={"status": "ok", "data": {}}),
        "get_files": AsyncMock(return_value={"status": "ok", "data": []}),
        "search_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs_total": AsyncMock(return_value={"status": "ok", "data": {}}),
        "get_task_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "download_file": AsyncMock(return_value=b"content"),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestSearchTasksFallback:
    """search_tasks should handle the case where neither query nor filter_query
    is provided — passing None to the client so all tasks are returned."""

    @pytest.mark.asyncio
    async def test_no_query_passes_none_filter(self):
        client = _make_client()
        mcp = FakeMCP()
        register_task_tools(mcp, client)

        await mcp.tools["search_tasks"](project_id="p1")

        client.search_tasks.assert_awaited_once_with(
            search_query=None,
            project_id="p1",
            task_id=None,
            email_user_from=None,
            email_user_to=None,
            status=None,
            extra=None,
        )


class TestGetProjectFilesValidation:
    """get_project_files requires at least one of project_id or task_id."""

    @pytest.mark.asyncio
    async def test_missing_both_ids_returns_error(self):
        client = _make_client()
        mcp = FakeMCP()
        register_file_tools(mcp, client)

        result = await mcp.tools["get_project_files"]()

        assert "error" in result
        client.get_files.assert_not_awaited()


class TestSearchTasksByTagErrorPath:
    """search_tasks_by_tag should handle API failures gracefully."""

    @pytest.mark.asyncio
    async def test_non_dict_tasks_data_returns_empty(self):
        """If get_tasks returns unexpected data, the tool should not crash."""
        client = _make_client(
            get_tasks=AsyncMock(return_value="unexpected-string"),
        )
        mcp = FakeMCP()
        register_tag_tools(mcp, client)

        result = await mcp.tools["search_tasks_by_tag"]("bug", "p1")

        assert result["count"] == 0
        assert result["error"] == "Failed to get tasks"


class TestGetTaskWithTagsFallback:
    """get_task_with_tags should handle a task without tags gracefully."""

    @pytest.mark.asyncio
    async def test_task_with_no_tags_key(self):
        client = _make_client(
            get_task=AsyncMock(return_value={"status": "ok", "data": {"name": "No Tags Task"}}),
        )
        mcp = FakeMCP()
        register_tag_tools(mcp, client)

        result = await mcp.tools["get_task_with_tags"]("t1")

        assert result["tag_names"] == []


class TestCostToolIsTimerFlag:
    """get_costs should pass is_timer to the client correctly."""

    @pytest.mark.asyncio
    async def test_is_timer_false_omits_param(self):
        client = _make_client()
        mcp = FakeMCP()
        register_timer_tools(mcp, client)

        await mcp.tools["get_costs"](project_id="p1", is_timer=False)

        call_kwargs = client.get_costs.await_args
        # is_timer=False should not set the flag
        assert call_kwargs.kwargs.get("is_timer") is False


class TestGetWebhooksScopeError:
    """get_webhooks should catch WorksectionAPIError and return a structured error dict."""

    @pytest.mark.asyncio
    async def test_permissions_error_returns_hint(self):
        client = _make_client(
            get_webhooks=AsyncMock(
                side_effect=WorksectionAPIError(
                    "Access denied: insufficient permissions for administrative"
                )
            ),
        )
        # register_system_tools needs a client with a settings attribute for health_check
        client.settings = SimpleNamespace(
            api_base_url="https://test.worksection.com/api/oauth2",
            worksection_account_url="https://test.worksection.com",
        )
        client.me = AsyncMock(return_value={"data": {"id": "1"}})
        mcp = FakeMCP()
        register_system_tools(mcp, client)

        result = await mcp.tools["get_webhooks"]()

        assert result["status"] == "error"
        assert "permissions" in result["error"].lower()
        assert "hint" in result
        assert "administrative" in result["hint"].lower()

    @pytest.mark.asyncio
    async def test_generic_api_error_no_hint(self):
        client = _make_client(
            get_webhooks=AsyncMock(side_effect=WorksectionAPIError("Server error 500")),
        )
        client.settings = SimpleNamespace(
            api_base_url="https://test.worksection.com/api/oauth2",
            worksection_account_url="https://test.worksection.com",
        )
        client.me = AsyncMock(return_value={"data": {"id": "1"}})
        mcp = FakeMCP()
        register_system_tools(mcp, client)

        result = await mcp.tools["get_webhooks"]()

        assert result["status"] == "error"
        assert "hint" not in result
