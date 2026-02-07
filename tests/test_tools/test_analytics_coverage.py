"""Tests for analytics tool edge cases: malformed dates, cross-project queries, time parsing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tests.helpers import FakeMCP
from worksection_mcp.tools.analytics import register_analytics_tools


def _make_client(**overrides: Any) -> Any:
    defaults: dict[str, Any] = {
        "get_all_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_users": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs": AsyncMock(return_value={"status": "ok", "data": []}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestOverdueTasksCrossProject:
    """get_overdue_tasks without a project_id should query all tasks via get_all_tasks."""

    @pytest.mark.asyncio
    async def test_no_project_queries_all_tasks(self):
        yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        client = _make_client(
            get_all_tasks=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {
                            "id": "t1",
                            "status": "active",
                            "date_end": yesterday,
                            "project": {"id": "p1", "name": "Alpha"},
                        },
                    ],
                }
            ),
        )

        mcp = FakeMCP()
        register_analytics_tools(mcp, client)

        result = await mcp.tools["get_overdue_tasks"]()

        client.get_all_tasks.assert_awaited_once()
        assert result["count"] == 1
        assert result["by_project"]["p1"]["count"] == 1


class TestMalformedDateHandling:
    """Tasks with un-parseable date_end values should be silently skipped,
    not crash the analytics pipeline."""

    @pytest.mark.asyncio
    async def test_project_stats_skips_bad_dates(self):
        client = _make_client(
            get_tasks=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"status": "active", "priority": 1, "date_end": "not-a-date"},
                        {"status": "active", "priority": 1, "date_end": ""},
                        {"status": "active", "priority": 1},  # no date_end at all
                    ],
                }
            ),
        )

        mcp = FakeMCP()
        register_analytics_tools(mcp, client)

        stats = await mcp.tools["get_project_stats"]("p1")

        assert stats["total_tasks"] == 3
        assert stats["overdue_tasks"] == 0  # none parseable as overdue
        assert stats["active_tasks"] == 3

    @pytest.mark.asyncio
    async def test_overdue_tasks_skips_bad_dates(self):
        client = _make_client(
            get_tasks=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"status": "active", "date_end": "31/12/2024"},  # wrong format
                        {"status": "active", "date_end": ""},
                    ],
                }
            ),
        )

        mcp = FakeMCP()
        register_analytics_tools(mcp, client)

        result = await mcp.tools["get_overdue_tasks"](project_id="p1")

        assert result["count"] == 0


class TestTeamWorkloadTimeParsing:
    """get_team_workload_summary must handle every time format the API can return:
    integer minutes, H:MM strings, and garbage values that should be treated as 0."""

    @pytest.mark.asyncio
    async def test_all_time_formats(self):
        client = _make_client(
            get_all_tasks=AsyncMock(return_value={"status": "ok", "data": []}),
            get_users=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"id": "u1", "first_name": "Ana", "last_name": "B", "email": "a@x.com"},
                    ],
                }
            ),
            get_costs=AsyncMock(
                return_value={
                    "status": "ok",
                    "data": [
                        {"user": {"id": "u1"}, "time": "2:15"},  # 135 minutes
                        {"user": {"id": "u1"}, "time": "30"},  # 30 minutes (string int)
                        {"user": {"id": "u1"}, "time": 45},  # 45 minutes (int)
                        {"user": {"id": "u1"}, "time": "bad"},  # 0 minutes (unparseable)
                    ],
                }
            ),
        )

        mcp = FakeMCP()
        register_analytics_tools(mcp, client)

        result = await mcp.tools["get_team_workload_summary"]()

        member = result["members"][0]
        assert member["time_logged_minutes"] == 135 + 30 + 45 + 0  # 210
        assert member["time_logged_hours"] == round(210 / 60, 2)

    @pytest.mark.asyncio
    async def test_cross_project_workload_uses_get_all_tasks(self):
        """When no project_id is given, get_all_tasks should be used for tasks."""
        client = _make_client(
            get_users=AsyncMock(return_value={"status": "ok", "data": []}),
            get_all_tasks=AsyncMock(return_value={"status": "ok", "data": []}),
            get_costs=AsyncMock(return_value={"status": "ok", "data": []}),
        )

        mcp = FakeMCP()
        register_analytics_tools(mcp, client)

        await mcp.tools["get_team_workload_summary"]()

        client.get_all_tasks.assert_awaited_once()
        client.get_tasks.assert_not_awaited()
