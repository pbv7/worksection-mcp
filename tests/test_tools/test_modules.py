"""Tests for MCP tool modules (excluding file-tool specific tests)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

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
        "get_contact_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_files": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_webhooks": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_task_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tags": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_project_tag_groups": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_events": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_costs_total": AsyncMock(return_value={"status": "ok", "total": {"time": "0:00"}}),
        "get_timers": AsyncMock(return_value={"status": "ok", "data": []}),
        "get_my_timer": AsyncMock(return_value={"status": "ok", "data": {}}),
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

    await mcp.tools["search_tasks"](query="report", project_id="p1", status="active")
    client.search_tasks.assert_awaited_with(
        search_query="name has 'report'",
        project_id="p1",
        task_id=None,
        email_user_from=None,
        email_user_to=None,
        status="active",
        extra=None,
    )

    discussion = await mcp.tools["get_task_discussion"]("t1")
    assert discussion["comment_count"] == 2


@pytest.mark.asyncio
async def test_user_and_activity_tools_aggregation():
    """User/activity tools should perform client-side filtering and grouping correctly."""
    activity_payload = {
        "status": "ok",
        "data": [
            {
                "object": {"type": "task"},
                "user_from": {"id": "u1"},
                "project": {"id": "p1", "name": "Alpha"},
            },
            {
                "object": {"type": "comment"},
                "user_from": {"id": "u1"},
                "project": {"id": "p1", "name": "Alpha"},
            },
            {
                "object": {"type": "task"},
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

    # get_user_assignments now uses server-side filtering via search_tasks
    # when email is available. Test fallback path (no email in user data).
    assignments = await mcp.tools["get_user_assignments"]("u1")
    assert assignments["task_count"] == 1
    assert assignments["tasks"][0]["id"] == "t1"

    # get_activity_log now includes event_types breakdown (consolidated from get_project_activity)
    activity_log = await mcp.tools["get_activity_log"](project_id="p1", period="7d")
    assert activity_log["event_types"] == {"task": 2, "comment": 1}
    assert activity_log["total_count"] == 3
    assert len(activity_log["events"]) == 3
    assert activity_log["truncation_reason"] == "none"

    user_activity = await mcp.tools["get_user_activity"]("u1", period="7d")
    assert len(user_activity["events"]) == 2
    assert user_activity["total_count"] == 2
    assert user_activity["returned_count"] == 2
    assert user_activity["truncation_reason"] == "none"
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
            return_value={"status": "ok", "data": [{"user_from": {"id": "u1"}, "time": "1:30"}]}
        ),
    )

    mcp = FakeMCP()
    register_analytics_tools(mcp, client)

    stats = await mcp.tools["get_project_stats"]("p1")
    assert stats["total_tasks"] == 3
    assert stats["completed_tasks"] == 1
    assert stats["overdue_tasks"] >= 1

    overdue_tasks = await mcp.tools["get_overdue_tasks"](project_id="p1")
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
        get_costs_total=AsyncMock(return_value={"status": "ok", "total": {"time": "2:15"}}),
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
    assert totals["total"]["time"] == "2:15"

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

    healthy = await mcp.tools["health_check"]()
    assert healthy["status"] == "healthy"
    assert healthy["token_valid"] is True
    assert healthy["api_reachable"] is True
    assert healthy["api_base_url"].endswith("/api/oauth2")
    assert healthy["account_url"] == "https://test.worksection.com"

    webhooks = await mcp.tools["get_webhooks"]()
    client.get_webhooks.assert_awaited_once()
    assert webhooks["status"] == "ok"

    failing_client = _make_client(me=AsyncMock(side_effect=RuntimeError("boom")))
    failing_mcp = FakeMCP()
    register_system_tools(failing_mcp, failing_client, oauth)

    unhealthy = await failing_mcp.tools["health_check"]()
    assert unhealthy["status"] == "unhealthy"
    assert "boom" in unhealthy["error"]


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
        get_contact_groups=AsyncMock(return_value={"status": "ok", "data": [{"id": "cg1"}]}),
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
    await mcp.tools["get_current_user"]()
    await mcp.tools["get_user_groups"]()
    await mcp.tools["get_contacts"]()
    await mcp.tools["get_contact_groups"]()
    await mcp.tools["get_task_tags"](group="g", tag_type="label", access="public")
    await mcp.tools["get_task_tag_groups"](tag_type="status", access="private")
    await mcp.tools["get_project_tags"](group="g", tag_type="label", access="public")
    await mcp.tools["get_project_tag_groups"](tag_type="status", access="private")
    await mcp.tools["get_comments"]("t1", include_files=True)
    discussion = await mcp.tools["get_task_discussion"]("t1")

    client.get_project.assert_any_await(project_id="p1", extra="text")
    client.get_project_groups.assert_awaited_once()
    client.get_all_tasks.assert_awaited_with(status_filter="active", extra="text")
    # status_filter='done' workaround: tool fetches with 'all' and filters client-side
    client.get_tasks.assert_any_await(project_id="p1", status_filter="all", extra="comments")
    client.get_task.assert_any_await(task_id="t1", extra="files")
    client.get_task.assert_any_await(task_id="t1", extra="subtasks")
    client.get_task.assert_any_await(task_id="t1", extra="relations")
    client.get_task.assert_any_await(task_id="t1", extra="subscribers")
    client.get_users.assert_awaited_with(status_filter="active")
    client.get_user.assert_awaited_with(user_id="u1")
    client.me.assert_awaited()
    client.get_user_groups.assert_awaited()
    client.get_contacts.assert_awaited()
    client.get_contact_groups.assert_awaited()
    client.get_task_tags.assert_awaited_with(group="g", tag_type="label", access="public")
    client.get_task_tag_groups.assert_awaited_with(tag_type="status", access="private")
    client.get_project_tags.assert_awaited_with(group="g", tag_type="label", access="public")
    client.get_project_tag_groups.assert_awaited_with(tag_type="status", access="private")
    client.get_comments.assert_any_await(task_id="t1", extra="files")
    assert discussion["comment_count"] == 1


@pytest.mark.asyncio
async def test_activity_period_validation():
    """Activity tools should return error dict for invalid period format."""
    client = _make_client()
    mcp = FakeMCP()
    register_activity_tools(mcp, client)

    result = await mcp.tools["get_activity_log"](period="invalid")
    assert "error" in result

    result2 = await mcp.tools["get_user_activity"]("u1", period="999d")
    assert "error" in result2


@pytest.mark.asyncio
async def test_search_tasks_with_filter_query():
    """search_tasks should use filter_query when provided, falling back to query."""
    client = _make_client()
    mcp = FakeMCP()
    register_task_tools(mcp, client)

    await mcp.tools["search_tasks"](filter_query="dateend < '2024-06-01'", project_id="p1")
    client.search_tasks.assert_awaited_with(
        search_query="dateend < '2024-06-01'",
        project_id="p1",
        task_id=None,
        email_user_from=None,
        email_user_to=None,
        status=None,
        extra=None,
    )


@pytest.mark.asyncio
async def test_get_user_assignments_server_side_filtering():
    """get_user_assignments should use search_tasks when email is available."""
    client = _make_client(
        get_user=AsyncMock(
            return_value={"status": "ok", "data": {"id": "u1", "email": "test@example.com"}}
        ),
        search_tasks=AsyncMock(return_value={"status": "ok", "data": [{"id": "t1"}, {"id": "t2"}]}),
    )
    mcp = FakeMCP()
    register_user_tools(mcp, client)

    result = await mcp.tools["get_user_assignments"]("u1")
    assert result["task_count"] == 2
    client.search_tasks.assert_awaited_with(email_user_to="test@example.com", status="active")
    # Should NOT have called get_all_tasks (server-side filtering used instead)
    client.get_all_tasks.assert_not_awaited()


@pytest.mark.asyncio
async def test_new_tools_exist():
    """New tools (get_contact_groups, get_project_files, get_webhooks, timers) should be registered."""
    client = _make_client()
    mcp = FakeMCP()
    register_user_tools(mcp, client)
    assert "get_contact_groups" in mcp.tools

    from worksection_mcp.tools.files import register_file_tools

    register_file_tools(mcp, client)
    assert "get_project_files" in mcp.tools

    register_system_tools(mcp, client)
    assert "get_webhooks" in mcp.tools

    register_timer_tools(mcp, client)
    assert "get_timers" in mcp.tools
    assert "get_my_timer" in mcp.tools


@pytest.mark.asyncio
async def test_timer_tools_call_client():
    """Timer tools should call corresponding client methods."""
    client = _make_client(
        get_timers=AsyncMock(
            return_value={
                "status": "ok",
                "data": [
                    {
                        "id": "1",
                        "time": "01:30:00",
                        "user_from": {"id": "u1"},
                        "task": {"id": "t1"},
                    }
                ],
            }
        ),
        get_my_timer=AsyncMock(
            return_value={"status": "ok", "data": {"time": 5400, "task": {"id": "t1"}}}
        ),
    )
    mcp = FakeMCP()
    register_timer_tools(mcp, client)

    timers = await mcp.tools["get_timers"]()
    assert timers["status"] == "ok"
    assert len(timers["data"]) == 1
    client.get_timers.assert_awaited_once()

    my_timer = await mcp.tools["get_my_timer"]()
    assert my_timer["status"] == "ok"
    assert my_timer["data"]["time"] == 5400
    client.get_my_timer.assert_awaited_once()


# --- Activity truncation tests (mock-based) ---


def _make_events(count: int, event_type: str = "task") -> dict:
    """Create a fake events payload with the given count."""
    return {
        "status": "ok",
        "data": [
            {
                "object": {"type": event_type},
                "user_from": {"id": "u1"},
                "project": {"id": "p1", "name": "Alpha"},
            }
            for _ in range(count)
        ],
    }


def _make_mixed_events(type_counts: dict[str, int]) -> dict:
    """Create events payload with mixed types."""
    events = [
        {
            "object": {"type": etype},
            "user_from": {"id": "u1"},
            "project": {"id": "p1", "name": "Alpha"},
        }
        for etype, count in type_counts.items()
        for _ in range(count)
    ]
    return {"status": "ok", "data": events}


@pytest.mark.asyncio
async def test_activity_truncation_size_cap_only():
    """Size-cap truncation should set truncation_reason='size_cap'."""
    client = _make_client(get_events=AsyncMock(return_value=_make_events(10)))
    mcp = FakeMCP()
    register_activity_tools(mcp, client)

    with patch("worksection_mcp.tools.activity.truncate_to_size") as mock_truncate:
        # Simulate size-cap truncation keeping only 5 items
        mock_truncate.side_effect = lambda data, **_kw: (data[:5], True)
        result = await mcp.tools["get_activity_log"](period="1d")

    assert result["total_count"] == 10
    assert result["returned_count"] == 5
    assert result["truncated"] is True
    assert result["truncation_reason"] == "size_cap"
    assert sum(result["event_types"].values()) == 10


@pytest.mark.asyncio
async def test_activity_truncation_both_max_results_and_size_cap():
    """Both max_results and size-cap should set truncation_reason='both'."""
    client = _make_client(get_events=AsyncMock(return_value=_make_events(10)))
    mcp = FakeMCP()
    register_activity_tools(mcp, client)

    with patch("worksection_mcp.tools.activity.truncate_to_size") as mock_truncate:
        # max_results=3 trims to 3, then size-cap further trims to 2
        mock_truncate.side_effect = lambda data, **_kw: (data[:2], True)
        result = await mcp.tools["get_activity_log"](period="1d", max_results=3)

    assert result["total_count"] == 10
    assert result["returned_count"] == 2
    assert result["truncated"] is True
    assert result["truncation_reason"] == "both"
    assert sum(result["event_types"].values()) == 10


@pytest.mark.asyncio
async def test_activity_no_truncation():
    """No truncation should set truncation_reason='none'."""
    client = _make_client(get_events=AsyncMock(return_value=_make_events(150)))
    mcp = FakeMCP()
    register_activity_tools(mcp, client)

    # No mock — use real truncate_to_size (150 small events won't exceed 850KB)
    result = await mcp.tools["get_activity_log"](period="1d")

    assert result["total_count"] == 150
    assert result["returned_count"] == 150
    assert result["truncated"] is False
    assert result["truncation_reason"] == "none"


@pytest.mark.asyncio
async def test_activity_event_types_computed_pre_truncation():
    """event_types should reflect the full set, not the truncated subset."""
    client = _make_client(
        get_events=AsyncMock(return_value=_make_mixed_events({"task": 6, "comment": 4}))
    )
    mcp = FakeMCP()
    register_activity_tools(mcp, client)

    with patch("worksection_mcp.tools.activity.truncate_to_size") as mock_truncate:
        mock_truncate.side_effect = lambda data, **_kw: (data[:3], True)
        result = await mcp.tools["get_activity_log"](period="1d")

    assert result["event_types"] == {"task": 6, "comment": 4}
    assert result["returned_count"] == 3
