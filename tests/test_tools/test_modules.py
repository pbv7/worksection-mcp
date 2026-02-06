"""Tests for MCP tool modules (excluding file-tool specific tests)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tests.helpers import FakeMCP
from worksection_mcp.tools import register_all_tools
from worksection_mcp.tools.activity import register_activity_tools
from worksection_mcp.tools.analytics import register_analytics_tools
from worksection_mcp.tools.comments import register_comment_tools
from worksection_mcp.tools.projects import register_project_tools
from worksection_mcp.tools.system import register_system_tools
from worksection_mcp.tools.tags import register_tag_tools
from worksection_mcp.tools.tasks import register_task_tools
from worksection_mcp.tools.timers import register_timer_tools
from worksection_mcp.tools.users import register_user_tools


def _make_client(**overrides: Any) -> Any:
    """Create a client-like object with async methods used by tools."""
    defaults: dict[str, Any] = {
        "settings": SimpleNamespace(
            api_base_url="https://test.worksection.com/api/oauth2",
            worksection_account_url="https://test.worksection.com",
        ),
        "get_projects": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project": AsyncMock(return_value={"status": "ok", "data": {}}),
        "get_project_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_all_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task": AsyncMock(return_value={"status": "ok", "data": {}}),
        "search_tasks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_comments": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_users": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_user": AsyncMock(return_value={"status": "ok", "data": {}}),
        "me": AsyncMock(return_value={"id": "u1", "name": "User"}),
        "get_user_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_contacts": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_events": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs_total": AsyncMock(return_value={"status": "ok", "data": {"total": 0}}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_register_all_tools_calls_each_registrar(monkeypatch):
    """register_all_tools should delegate registration to all module registrars."""
    calls = []

    def _mark(name):
        def _call(*args):
            calls.append((name, args))

        return _call

    monkeypatch.setattr("worksection_mcp.tools.register_project_tools", _mark("projects"))
    monkeypatch.setattr("worksection_mcp.tools.register_task_tools", _mark("tasks"))
    monkeypatch.setattr("worksection_mcp.tools.register_comment_tools", _mark("comments"))
    monkeypatch.setattr("worksection_mcp.tools.register_file_tools", _mark("files"))
    monkeypatch.setattr("worksection_mcp.tools.register_timer_tools", _mark("timers"))
    monkeypatch.setattr("worksection_mcp.tools.register_user_tools", _mark("users"))
    monkeypatch.setattr("worksection_mcp.tools.register_tag_tools", _mark("tags"))
    monkeypatch.setattr("worksection_mcp.tools.register_analytics_tools", _mark("analytics"))
    monkeypatch.setattr("worksection_mcp.tools.register_activity_tools", _mark("activity"))
    monkeypatch.setattr("worksection_mcp.tools.register_system_tools", _mark("system"))

    mcp = FakeMCP()
    client = object()
    oauth = object()
    file_cache = object()
    register_all_tools(mcp, client, oauth, file_cache)

    assert [name for name, _ in calls] == [
        "projects",
        "tasks",
        "comments",
        "files",
        "timers",
        "users",
        "tags",
        "analytics",
        "activity",
        "system",
    ]


@pytest.mark.asyncio
async def test_project_task_and_comment_tools_behavior():
    """Project/task/comment tools should call client APIs with expected params."""
    client = _make_client(
        get_task=AsyncMock(
            side_effect=[
                {"status": "ok", "data": {"id": "t1"}},
                {"status": "ok", "data": {"id": "t1", "files": []}},
                {"status": "ok", "data": {"id": "t1", "text": "description"}},
            ]
        ),
        get_comments=AsyncMock(
            return_value={
                "status": "ok",
                "data": [
                    {"id": "c1", "text": "A", "files": [{"id": "f1", "name": "shot.png"}]},
                    {"id": "c2", "text": "B", "files": [{"id": "f2", "name": "note.txt"}]},
                ],
            }
        ),
    )

    mcp = FakeMCP()
    register_project_tools(mcp, client)
    register_task_tools(mcp, client)
    register_comment_tools(mcp, client)

    await mcp.tools["get_projects"](status_filter="active", extra="users")
    client.get_projects.assert_awaited_with(status_filter="active", extra="users")

    await mcp.tools["get_project_team"]("p1")
    client.get_project.assert_awaited_with(project_id="p1", extra="users")

    await mcp.tools["search_tasks"]("report", project_id="p1", status="active")
    client.search_tasks.assert_awaited_with(
        search_query="name has 'report'",
        project_id="p1",
        email_user_from=None,
        email_user_to=None,
        status="active",
        extra=None,
    )

    combined = await mcp.tools["get_task_with_comments_and_files"]("t1")
    assert combined["status"] == "ok"
    assert combined["comments"][0]["id"] == "c1"

    with_images = await mcp.tools["get_comments_with_images"]("t1")
    assert with_images["total_images"] == 1
    assert with_images["comments_with_images"][0]["id"] == "c1"


@pytest.mark.asyncio
async def test_user_and_activity_tools_aggregation():
    """User/activity tools should perform client-side filtering and grouping correctly."""
    activity_payload = {
        "status": "ok",
        "data": [
            {
                "type": "task_create",
                "user_from": {"id": "u1"},
                "project": {"id": "p1", "name": "Alpha"},
            },
            {
                "type": "task_update",
                "user_from": {"id": "u1"},
                "project": {"id": "p1", "name": "Alpha"},
            },
            {
                "type": "task_create",
                "user_from": {"id": "u2"},
                "project": {"id": "p2", "name": "Beta"},
            },
        ],
    }
    client = _make_client(
        get_all_tasks=AsyncMock(
            return_value={
                "status": "ok",
                "data": [
                    {"id": "t1", "user_to": {"id": "u1"}},
                    {"id": "t2", "user_to": {"id": "u2"}},
                ],
            }
        ),
        get_events=AsyncMock(return_value=activity_payload),
    )

    mcp = FakeMCP()
    register_user_tools(mcp, client)
    register_activity_tools(mcp, client)

    assignments = await mcp.tools["get_user_assignments"]("u1")
    assert assignments["task_count"] == 1
    assert assignments["tasks"][0]["id"] == "t1"

    project_activity = await mcp.tools["get_project_activity"]("p1")
    assert project_activity["event_types"] == {"task_create": 2, "task_update": 1}

    user_activity = await mcp.tools["get_user_activity"]("u1")
    assert len(user_activity["events"]["data"]) == 2
    assert user_activity["projects_touched"]["p1"]["event_count"] == 2


@pytest.mark.asyncio
async def test_analytics_tools_compute_counts_and_workload():
    """Analytics tools should compute overdue/completion/workload metrics."""
    now = datetime.now(UTC)
    overdue = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    future = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    client = _make_client(
        get_tasks=AsyncMock(
            side_effect=[
                {
                    "status": "ok",
                    "data": [
                        {"status": "done", "priority": 1, "date_end": overdue},
                        {"status": "active", "priority": 2, "date_end": overdue},
                        {"status": "active", "priority": 2, "date_end": future},
                    ],
                },
                {
                    "status": "ok",
                    "data": [{"status": "active", "date_end": overdue, "project": {"id": "p1"}}],
                },
                {"status": "ok", "data": [{"status": "DONE"}, {"status": "active"}]},
                {"status": "ok", "data": [{"priority": 5}, {"priority": 4}, {"priority": "5"}]},
                {
                    "status": "ok",
                    "data": [
                        {"user_to": {"id": "u1"}, "status": "done"},
                        {"user_to": {"id": "u1"}, "status": "active"},
                    ],
                },
            ]
        ),
        get_users=AsyncMock(
            return_value={
                "status": "ok",
                "data": [
                    {"id": "u1", "first_name": "Ana", "last_name": "Test", "email": "a@example.com"}
                ],
            }
        ),
        get_costs=AsyncMock(
            return_value={"status": "ok", "data": [{"user": {"id": "u1"}, "time": "1:30"}]}
        ),
    )

    mcp = FakeMCP()
    register_analytics_tools(mcp, client)

    stats = await mcp.tools["get_project_stats"]("p1")
    assert stats["total_tasks"] == 3
    assert stats["completed_tasks"] == 1
    assert stats["overdue_tasks"] >= 1

    overdue_tasks = await mcp.tools["get_overdue_tasks"]("p1")
    assert overdue_tasks["count"] == 1

    by_status = await mcp.tools["get_tasks_by_status"]("p1", "done")
    assert by_status["count"] == 1

    by_priority = await mcp.tools["get_tasks_by_priority"]("p1", 5)
    assert by_priority["count"] == 2

    workload = await mcp.tools["get_team_workload_summary"]("p1")
    assert workload["total_members"] == 1
    assert workload["members"][0]["time_logged_minutes"] == 90


@pytest.mark.asyncio
async def test_tag_tools_and_timer_tools():
    """Tag/timer tools should transform data and return filtered summaries."""
    client = _make_client(
        get_task=AsyncMock(
            return_value={"status": "ok", "data": {"name": "Task", "tags": {"1": "Bug"}}}
        ),
        get_tasks=AsyncMock(
            return_value={
                "status": "ok",
                "data": [
                    {"id": "t1", "tags": {"1": "Bug"}},
                    {"id": "t2", "tags": {"2": "Feature"}},
                ],
            }
        ),
        get_costs=AsyncMock(
            return_value={
                "status": "ok",
                "data": [
                    {
                        "time": "1:30",
                        "project": {"id": "p1", "name": "Alpha"},
                        "task": {"id": "t1", "name": "A"},
                    },
                    {
                        "time": "45",
                        "project": {"id": "p1", "name": "Alpha"},
                        "task": {"id": "t1", "name": "A"},
                    },
                    {
                        "time": "bad",
                        "project": {"id": "p2", "name": "Beta"},
                        "task": {"id": "t2", "name": "B"},
                    },
                ],
            }
        ),
        get_costs_total=AsyncMock(return_value={"status": "ok", "summary": {"total_time": 135}}),
    )

    mcp = FakeMCP()
    register_tag_tools(mcp, client)
    register_timer_tools(mcp, client)

    task_with_tags = await mcp.tools["get_task_with_tags"]("t1")
    assert task_with_tags["tag_names"] == ["Bug"]

    found = await mcp.tools["search_tasks_by_tag"]("bug", "p1")
    assert found["count"] == 1
    assert found["tasks"][0]["id"] == "t1"

    totals = await mcp.tools["get_costs_total"]("p1", "2024-01-01", "2024-01-31")
    assert totals["project_id"] == "p1"
    assert totals["summary"]["total_time"] == 135

    user_workload = await mcp.tools["get_user_workload"]("u1", "2024-01-01", "2024-01-31")
    assert user_workload["total_time_minutes"] == 135
    assert user_workload["by_project"]["p1"]["time"] == 135

    report = await mcp.tools["get_project_time_report"]("p1")
    assert report["project_id"] == "p1"
    assert "totals" in report
    assert "entries" in report


@pytest.mark.asyncio
async def test_system_tools_health_and_status_paths():
    """System tools should reflect API reachability and oauth status correctly."""
    oauth: Any = SimpleNamespace(
        get_valid_token=AsyncMock(return_value="token"),
        get_user_info=AsyncMock(return_value={"email": "u@example.com"}),
    )
    client = _make_client(me=AsyncMock(return_value={"id": "u1"}))
    mcp = FakeMCP()
    register_system_tools(mcp, client, oauth)

    account = await mcp.tools["get_account_info"]()
    assert account["authenticated"] is True

    healthy = await mcp.tools["health_check"]()
    assert healthy["status"] == "healthy"
    assert healthy["token_valid"] is True
    assert healthy["api_reachable"] is True

    current = await mcp.tools["get_current_user_info"]()
    assert current["oauth_info"]["email"] == "u@example.com"
    assert current["api_info"]["id"] == "u1"

    status = await mcp.tools["get_api_status"]()
    assert status["api_reachable"] is True
    assert status["api_base_url"].endswith("/api/oauth2")

    failing_client = _make_client(me=AsyncMock(side_effect=RuntimeError("boom")))
    failing_mcp = FakeMCP()
    register_system_tools(failing_mcp, failing_client, oauth)

    unhealthy = await failing_mcp.tools["health_check"]()
    assert unhealthy["status"] == "unhealthy"
    assert "boom" in unhealthy["error"]

    api_down = await failing_mcp.tools["get_api_status"]()
    assert api_down["api_reachable"] is False


@pytest.mark.asyncio
async def test_project_task_user_tag_and_comment_wrappers():
    """Wrapper tools should delegate to corresponding client calls with expected args."""
    client = _make_client(
        get_project=AsyncMock(return_value={"status": "ok", "data": {"id": "p1"}}),
        get_project_groups=AsyncMock(return_value={"status": "ok", "data": [{"id": "g1"}]}),
        get_all_tasks=AsyncMock(return_value={"status": "ok", "data": []}),
        get_tasks=AsyncMock(return_value={"status": "ok", "data": []}),
        get_task=AsyncMock(return_value={"status": "ok", "data": {"id": "t1"}}),
        get_comments=AsyncMock(return_value={"status": "ok", "data": [{"id": "c1"}]}),
        get_users=AsyncMock(return_value={"status": "ok", "data": [{"id": "u1"}]}),
        get_user=AsyncMock(return_value={"status": "ok", "data": {"id": "u1"}}),
        me=AsyncMock(return_value={"id": "u1"}),
        get_user_groups=AsyncMock(return_value={"status": "ok", "data": [{"id": "team"}]}),
        get_contacts=AsyncMock(return_value={"status": "ok", "data": [{"id": "contact"}]}),
        get_task_tags=AsyncMock(return_value={"status": "ok", "data": []}),
        get_task_tag_groups=AsyncMock(return_value={"status": "ok", "data": []}),
        get_project_tags=AsyncMock(return_value={"status": "ok", "data": []}),
        get_project_tag_groups=AsyncMock(return_value={"status": "ok", "data": []}),
        search_tasks=AsyncMock(return_value={"status": "ok", "data": []}),
    )

    mcp = FakeMCP()
    register_project_tools(mcp, client)
    register_task_tools(mcp, client)
    register_user_tools(mcp, client)
    register_tag_tools(mcp, client)
    register_comment_tools(mcp, client)

    await mcp.tools["get_project"]("p1", extra="text")
    await mcp.tools["get_project_groups"]()
    await mcp.tools["get_all_tasks"](status_filter="active", extra="text")
    await mcp.tools["get_tasks"]("p1", status_filter="done", extra="comments")
    await mcp.tools["get_task"]("t1", extra="files")
    await mcp.tools["get_task_subtasks"]("t1")
    await mcp.tools["get_task_relations"]("t1")
    await mcp.tools["get_task_subscribers"]("t1")
    await mcp.tools["get_users"](status_filter="active")
    await mcp.tools["get_user"]("u1")
    await mcp.tools["me"]()
    await mcp.tools["get_user_groups"]()
    await mcp.tools["get_contacts"]()
    await mcp.tools["get_task_tags"](group="g", tag_type="label", access="public")
    await mcp.tools["get_task_tag_groups"](tag_type="status", access="private")
    await mcp.tools["get_project_tags"](group="g", tag_type="label", access="public")
    await mcp.tools["get_project_tag_groups"](tag_type="status", access="private")
    await mcp.tools["get_comments"]("t1", include_files=True)
    discussion = await mcp.tools["get_task_discussion"]("t1")

    client.get_project.assert_any_await(project_id="p1", extra="text")
    client.get_project_groups.assert_awaited_once()
    client.get_all_tasks.assert_awaited_with(status_filter="active", extra="text")
    client.get_tasks.assert_any_await(project_id="p1", status_filter="done", extra="comments")
    client.get_task.assert_any_await(task_id="t1", extra="files")
    client.get_task.assert_any_await(task_id="t1", extra="subtasks")
    client.get_task.assert_any_await(task_id="t1", extra="relations")
    client.get_task.assert_any_await(task_id="t1", extra="subscribers")
    client.get_users.assert_awaited_with(status_filter="active")
    client.get_user.assert_awaited_with(user_id="u1")
    client.me.assert_awaited()
    client.get_user_groups.assert_awaited()
    client.get_contacts.assert_awaited()
    client.get_task_tags.assert_awaited_with(group="g", tag_type="label", access="public")
    client.get_task_tag_groups.assert_awaited_with(tag_type="status", access="private")
    client.get_project_tags.assert_awaited_with(group="g", tag_type="label", access="public")
    client.get_project_tag_groups.assert_awaited_with(tag_type="status", access="private")
    client.get_comments.assert_any_await(task_id="t1", extra="files")
    assert discussion["comment_count"] == 1
