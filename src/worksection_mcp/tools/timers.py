"""Cost and time tracking MCP tools."""

import logging

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar
from worksection_mcp.utils.date_utils import validate_date_range

logger = logging.getLogger(__name__)


def register_timer_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register cost and time tracking tools with the MCP server."""

    @mcp.tool()
    async def get_timers() -> dict:
        """Get all currently running timers.

        Returns:
            List of active timers with:
            - id: Timer record ID
            - time: Elapsed time as "HH:MM:SS"
            - user_from: User who started the timer
            - task: Associated task info
        """
        return await client.get_timers()

    @mcp.tool()
    async def get_my_timer() -> dict:
        """Get the current user's running timer.

        Returns:
            Current timer info:
            - time: Elapsed time in seconds (integer)
            - task: Associated task info
        """
        return await client.get_my_timer()

    @mcp.tool()
    async def get_costs(
        project_id: str | None = None,
        task_id: str | None = None,
        user_id: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        is_timer: bool | None = None,
    ) -> dict:
        """Get time/cost records with flexible filtering.

        Note: The API's user_id parameter may not filter correctly.
        When user_id is provided, client-side filtering is applied to
        ensure accurate results.

        Args:
            project_id: Filter by project
            task_id: Filter by task
            user_id: Filter by user
            date_start: Start date (YYYY-MM-DD or DD.MM.YYYY format)
            date_end: End date (YYYY-MM-DD or DD.MM.YYYY format)
            is_timer: True for timer entries, False for manual entries

        Returns:
            List of cost/time records:
            - id: Record ID
            - user_from: Who logged the time
            - task: Associated task
            - time: Time logged (minutes or hours)
            - money: Cost amount
            - date: Date of entry
            - comment: Entry description
        """
        validate_date_range(date_start, date_end)

        result = await client.get_costs(
            project_id=project_id,
            task_id=task_id,
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            is_timer=is_timer,
        )

        # Client-side user filtering (API may not filter correctly)
        if user_id and isinstance(result, dict) and "data" in result:
            original_count = len(result["data"])
            result["data"] = [
                entry
                for entry in result["data"]
                if str(entry.get("user_from", {}).get("id")) == str(user_id)
            ]
            if len(result["data"]) != original_count:
                logger.debug(
                    "Client-side user filtering applied: %d -> %d entries",
                    original_count,
                    len(result["data"]),
                )

        return result

    @mcp.tool()
    async def get_costs_total(
        project_id: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> dict:
        """Get aggregated cost/time totals.

        Args:
            project_id: Filter by project
            date_start: Start date (YYYY-MM-DD or DD.MM.YYYY format)
            date_end: End date (YYYY-MM-DD or DD.MM.YYYY format)

        Returns:
            Aggregated totals:
            - project_id: The project ID (if specified)
            - total_time: Total time logged
            - total_cost: Total cost amount
            - by_user: Breakdown by user
            - by_project: Breakdown by project (if no project filter)
        """
        validate_date_range(date_start, date_end)

        result = await client.get_costs_total(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
        )
        # Include project_id in response for validation
        return {
            "project_id": project_id,
            "date_start": date_start,
            "date_end": date_end,
            **result,
        }

    @mcp.tool()
    async def get_user_workload(
        user_id: str,
        date_start: str,
        date_end: str,
    ) -> dict:
        """Get time entries for a specific user in a date range.

        Useful for generating individual performance/workload reports.

        Args:
            user_id: The user ID to get workload for
            date_start: Start date (YYYY-MM-DD or DD.MM.YYYY format)
            date_end: End date (YYYY-MM-DD or DD.MM.YYYY format)

        Returns:
            User's time entries for the period:
            - entries: List of time records
            - total_time: Sum of all time logged
            - by_project: Time breakdown by project
            - by_task: Time breakdown by task
        """
        validate_date_range(date_start, date_end)

        costs_data = await client.get_costs(
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
        )

        # Calculate aggregations
        total_time = 0
        by_project = {}
        by_task = {}

        if isinstance(costs_data, dict) and "data" in costs_data:
            for entry in costs_data["data"]:
                time_val = entry.get("time", 0)
                if isinstance(time_val, str):
                    # Parse time string (could be "1:30" or "90")
                    try:
                        if ":" in time_val:
                            hours, mins = time_val.split(":")
                            time_val = int(hours) * 60 + int(mins)
                        else:
                            time_val = int(time_val)
                    except ValueError:
                        time_val = 0

                total_time += time_val

                # Aggregate by project
                project = entry.get("project", {})
                project_id = project.get("id", "unknown")
                project_name = project.get("name", "Unknown")
                if project_id not in by_project:
                    by_project[project_id] = {"name": project_name, "time": 0}
                by_project[project_id]["time"] += time_val

                # Aggregate by task
                task = entry.get("task", {})
                task_id = task.get("id", "unknown")
                task_name = task.get("name", "Unknown")
                if task_id not in by_task:
                    by_task[task_id] = {"name": task_name, "time": 0}
                by_task[task_id]["time"] += time_val

        return {
            "user_id": user_id,
            "date_start": date_start,
            "date_end": date_end,
            "entries": costs_data,
            "total_time_minutes": total_time,
            "total_time_hours": round(total_time / 60, 2),
            "by_project": by_project,
            "by_task": by_task,
        }

    @mcp.tool()
    async def get_project_time_report(
        project_id: str,
        date_start: str | None = None,
        date_end: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """Get time tracking report for a project.

        Args:
            project_id: The project ID
            date_start: Start date (YYYY-MM-DD or DD.MM.YYYY format, optional)
            date_end: End date (YYYY-MM-DD or DD.MM.YYYY format, optional)
            user_id: Filter by user (optional, applied client-side)

        Returns:
            Project time report:
            - project_id: Project ID
            - total_time: Total time logged
            - by_user: Time breakdown by team member
            - by_task: Time breakdown by task
            - entries: Individual time entries
        """
        validate_date_range(date_start, date_end)

        costs_data = await client.get_costs(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
        )

        # Client-side user filtering
        if user_id and isinstance(costs_data, dict) and "data" in costs_data:
            original_count = len(costs_data["data"])
            costs_data["data"] = [
                entry
                for entry in costs_data["data"]
                if str(entry.get("user_from", {}).get("id")) == str(user_id)
            ]
            if len(costs_data["data"]) != original_count:
                logger.debug(
                    "Client-side user filtering for project report: %d -> %d entries",
                    original_count,
                    len(costs_data["data"]),
                )

        def _parse_time_minutes(val: object) -> int:
            """Parse a time value to minutes."""
            if isinstance(val, int):
                return val
            if isinstance(val, str):
                try:
                    if ":" in val:
                        hours, mins = val.split(":")
                        return int(hours) * 60 + int(mins)
                    return int(val)
                except ValueError:
                    return 0
            return 0

        # Only fetch totals if not filtering by user (API totals include all users)
        if user_id:
            # Recompute totals from filtered entries
            total_time_minutes = 0
            if isinstance(costs_data, dict) and "data" in costs_data:
                for entry in costs_data["data"]:
                    total_time_minutes += _parse_time_minutes(entry.get("time", 0))
            totals_data: dict = {
                "total_time_minutes": total_time_minutes,
                "total_time_hours": round(total_time_minutes / 60, 2),
                "filtered_by_user": user_id,
                "source": "recomputed",
            }
        else:
            totals_raw = await client.get_costs_total(
                project_id=project_id,
                date_start=date_start,
                date_end=date_end,
            )
            raw_val: object = 0
            found = False
            if isinstance(totals_raw, dict):
                # Primary: documented API shape {"total": {"time": "103:39"}}
                total_obj = totals_raw.get("total")
                if isinstance(total_obj, dict) and "time" in total_obj:
                    raw_val = total_obj["time"]
                    found = True
                # Fallback: alternative response shapes
                if not found:
                    data = totals_raw.get("data")
                    if isinstance(data, dict):
                        for key in ("total_time_minutes", "total_time"):
                            if key in data:
                                raw_val = data[key]
                                found = True
                                break
                        if not found:
                            summary = data.get("summary")
                            if isinstance(summary, dict) and "total_time" in summary:
                                raw_val = summary["total_time"]
                                found = True
            total_time_minutes = _parse_time_minutes(raw_val)
            totals_data = {
                "total_time_minutes": total_time_minutes,
                "total_time_hours": round(total_time_minutes / 60, 2),
                "filtered_by_user": None,
                "source": "api",
                "totals_raw": totals_raw,
            }

        return {
            "project_id": project_id,
            "date_start": date_start,
            "date_end": date_end,
            "totals": totals_data,
            "entries": costs_data,
        }
