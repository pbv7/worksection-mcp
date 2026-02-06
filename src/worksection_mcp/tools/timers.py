"""Time tracking MCP tools."""

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar


def register_timer_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register time tracking tools with the MCP server.

    Note: Timer-specific tools (get_timers, get_my_timer) have been removed
    because Worksection API doesn't provide a timers_read scope. Only cost/time
    tracking tools that use the costs_read scope are available.
    """

    # NOTE: get_timers and get_my_timer removed - no timers_read scope available
    # The Worksection API only provides costs_read scope for time tracking data

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
            - user: Who logged the time
            - task: Associated task
            - time: Time logged (minutes or hours)
            - money: Cost amount
            - date: Date of entry
            - comment: Entry description
        """
        return await client.get_costs(
            project_id=project_id,
            task_id=task_id,
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            is_timer=is_timer,
        )

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
    ) -> dict:
        """Get time tracking report for a project.

        Args:
            project_id: The project ID
            date_start: Start date (YYYY-MM-DD or DD.MM.YYYY format, optional)
            date_end: End date (YYYY-MM-DD or DD.MM.YYYY format, optional)

        Returns:
            Project time report:
            - project_id: Project ID
            - total_time: Total time logged
            - by_user: Time breakdown by team member
            - by_task: Time breakdown by task
            - entries: Individual time entries
        """
        costs_data = await client.get_costs(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
        )

        totals_data = await client.get_costs_total(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
        )

        return {
            "project_id": project_id,
            "date_start": date_start,
            "date_end": date_end,
            "totals": totals_data,
            "entries": costs_data,
        }
