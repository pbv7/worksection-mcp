"""Tests for tool-level edge cases: search_tasks fallback, project_files validation, tag errors."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tests.helpers import FakeMCP
from worksection_mcp.client.api import WorksectionAPIError
from worksection_mcp.tools.comments import register_comment_tools
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
        "get_comments": AsyncMock(return_value={"status": "ok", "data": []}),
        "search_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs_total": AsyncMock(return_value={"status": "ok", "data": {}}),
        "get_task_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_timers": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_my_timer": AsyncMock(return_value={"status": "ok", "data": {}}),
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


class TestMaxResultsValidation:
    """max_results <= 0 should raise ValueError for search_tasks and get_comments."""

    @pytest.mark.asyncio
    async def test_search_tasks_negative_max_results(self):
        client = _make_client()
        mcp = FakeMCP()
        register_task_tools(mcp, client)

        with pytest.raises(ValueError, match="max_results must be a positive integer"):
            await mcp.tools["search_tasks"](project_id="p1", max_results=0)

    @pytest.mark.asyncio
    async def test_search_tasks_zero_max_results(self):
        client = _make_client()
        mcp = FakeMCP()
        register_task_tools(mcp, client)

        with pytest.raises(ValueError, match="max_results must be a positive integer"):
            await mcp.tools["search_tasks"](project_id="p1", max_results=-1)

    @pytest.mark.asyncio
    async def test_get_comments_negative_max_results(self):
        client = _make_client(
            get_comments=AsyncMock(return_value={"status": "ok", "data": []}),
        )
        mcp = FakeMCP()
        register_comment_tools(mcp, client)

        with pytest.raises(ValueError, match="max_results must be a positive integer"):
            await mcp.tools["get_comments"]("t1", max_results=0)

    @pytest.mark.asyncio
    async def test_search_tasks_none_max_results_returns_all(self):
        """max_results=None should return all results without truncation."""
        client = _make_client(
            search_tasks=AsyncMock(
                return_value={"status": "ok", "data": [{"id": f"t{i}"} for i in range(200)]}
            ),
        )
        mcp = FakeMCP()
        register_task_tools(mcp, client)

        result = await mcp.tools["search_tasks"](project_id="p1", max_results=None)
        assert result["total_count"] == 200
        assert result["returned_count"] == 200
        assert result["truncated"] is False


class TestListImageAttachmentsValidation:
    """list_image_attachments must have exactly one of task_id or project_id."""

    @pytest.mark.asyncio
    async def test_both_ids_raises_error(self):
        client = _make_client()
        mcp = FakeMCP()
        register_file_tools(mcp, client)

        with pytest.raises(ValueError, match="Provide either task_id or project_id"):
            await mcp.tools["list_image_attachments"](task_id="t1", project_id="p1")

    @pytest.mark.asyncio
    async def test_neither_id_raises_error(self):
        client = _make_client()
        mcp = FakeMCP()
        register_file_tools(mcp, client)

        with pytest.raises(ValueError, match="Either task_id or project_id is required"):
            await mcp.tools["list_image_attachments"]()

    @pytest.mark.asyncio
    async def test_project_id_filters_images(self):
        client = _make_client(
            get_files=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"id": "f1", "name": "photo.jpg"},
                        {"id": "f2", "name": "document.pdf"},
                        {"id": "f3", "name": "screenshot.png"},
                    ],
                }
            ),
        )
        mcp = FakeMCP()
        register_file_tools(mcp, client)

        result = await mcp.tools["list_image_attachments"](project_id="p1")
        assert result["image_count"] == 2
        assert result["project_id"] == "p1"
        names = {img["name"] for img in result["images"]}
        assert names == {"photo.jpg", "screenshot.png"}


class TestGetCostsUserFiltering:
    """get_costs should filter entries by user_id client-side."""

    @pytest.mark.asyncio
    async def test_user_id_filters_mixed_user_payload(self):
        client = _make_client(
            get_costs=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"time": "1:30", "user_from": {"id": "u1"}, "task": {"id": "t1"}},
                        {"time": "45", "user_from": {"id": "u2"}, "task": {"id": "t2"}},
                        {"time": "2:00", "user_from": {"id": "u1"}, "task": {"id": "t3"}},
                    ],
                }
            ),
        )
        mcp = FakeMCP()
        register_timer_tools(mcp, client)

        result = await mcp.tools["get_costs"](project_id="p1", user_id="u1")

        entries = result["data"]
        assert len(entries) == 2
        assert all(e["user_from"]["id"] == "u1" for e in entries)


class TestGetProjectTimeReportTotalsContract:
    """get_project_time_report totals should have a normalized shape."""

    COMMON_KEYS: frozenset[str] = frozenset(
        {"total_time_minutes", "total_time_hours", "filtered_by_user", "source"}
    )

    @pytest.mark.asyncio
    async def test_recomputed_totals_with_user_id(self):
        client = _make_client(
            get_costs=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"time": "1:30", "user_from": {"id": "u1"}},
                        {"time": 45, "user_from": {"id": "u1"}},
                    ],
                }
            ),
        )
        mcp = FakeMCP()
        register_timer_tools(mcp, client)

        result = await mcp.tools["get_project_time_report"]("p1", user_id="u1")
        totals = result["totals"]

        assert set(totals.keys()) >= self.COMMON_KEYS
        assert totals["source"] == "recomputed"
        assert totals["filtered_by_user"] == "u1"
        assert totals["total_time_minutes"] == 135  # 90 + 45
        assert totals["total_time_hours"] == 2.25
        assert "totals_raw" not in totals

    @pytest.mark.asyncio
    async def test_api_totals_without_user_id(self):
        client = _make_client(
            get_costs=AsyncMock(return_value={"status": "ok", "data": []}),
            get_costs_total=AsyncMock(return_value={"status": "ok", "total": {"time": "2:00"}}),
        )
        mcp = FakeMCP()
        register_timer_tools(mcp, client)

        result = await mcp.tools["get_project_time_report"]("p1")
        totals = result["totals"]

        assert set(totals.keys()) >= self.COMMON_KEYS
        assert totals["source"] == "api"
        assert totals["filtered_by_user"] is None
        assert totals["total_time_minutes"] == 120
        assert totals["total_time_hours"] == 2.0
        assert "totals_raw" in totals

    @pytest.mark.asyncio
    async def test_both_branches_have_same_common_keys(self):
        client_recomputed = _make_client(
            get_costs=AsyncMock(
                return_value={"status": "ok", "data": [{"time": 60, "user_from": {"id": "u1"}}]}
            ),
        )
        client_api = _make_client(
            get_costs=AsyncMock(return_value={"status": "ok", "data": []}),
            get_costs_total=AsyncMock(return_value={"status": "ok", "total": {"time": "1:00"}}),
        )

        mcp1 = FakeMCP()
        register_timer_tools(mcp1, client_recomputed)
        result1 = await mcp1.tools["get_project_time_report"]("p1", user_id="u1")

        mcp2 = FakeMCP()
        register_timer_tools(mcp2, client_api)
        result2 = await mcp2.tools["get_project_time_report"]("p1")

        common1 = set(result1["totals"].keys()) - {"totals_raw"}
        common2 = set(result2["totals"].keys()) - {"totals_raw"}
        assert common1 == common2

    @pytest.mark.asyncio
    async def test_api_zero_time_does_not_fallthrough(self):
        """Zero time in primary path must NOT fall through to fallback paths."""
        client = _make_client(
            get_costs=AsyncMock(return_value={"status": "ok", "data": []}),
            get_costs_total=AsyncMock(
                return_value={
                    "status": "ok",
                    "total": {"time": "0:00"},
                    "data": {"total_time_minutes": 999},
                }
            ),
        )
        mcp = FakeMCP()
        register_timer_tools(mcp, client)

        result = await mcp.tools["get_project_time_report"]("p1")
        assert result["totals"]["total_time_minutes"] == 0

    @pytest.mark.asyncio
    async def test_api_fallback_data_shape(self):
        """Fallback data.total_time_minutes path should work when total key is absent."""
        client = _make_client(
            get_costs=AsyncMock(return_value={"status": "ok", "data": []}),
            get_costs_total=AsyncMock(
                return_value={"status": "ok", "data": {"total_time_minutes": 60}}
            ),
        )
        mcp = FakeMCP()
        register_timer_tools(mcp, client)

        result = await mcp.tools["get_project_time_report"]("p1")
        assert result["totals"]["total_time_minutes"] == 60


class TestGetTasksDoneWorkaround:
    """get_tasks with status_filter='done' should apply client-side filtering."""

    @pytest.mark.asyncio
    async def test_done_filter_uses_client_side_filtering(self):
        client = _make_client(
            get_tasks=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"id": "t1", "status": "done"},
                        {"id": "t2", "status": "active"},
                        {"id": "t3", "status": "closed"},
                    ],
                }
            ),
        )
        mcp = FakeMCP()
        register_task_tools(mcp, client)

        result = await mcp.tools["get_tasks"]("p1", status_filter="done")

        # Should have called with status_filter="all"
        client.get_tasks.assert_awaited_once_with(project_id="p1", status_filter="all", extra=None)
        # Should have filtered to done/closed only
        assert len(result["data"]) == 2
        ids = {t["id"] for t in result["data"]}
        assert ids == {"t1", "t3"}
