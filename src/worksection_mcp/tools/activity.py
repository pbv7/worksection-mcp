"""Activity and event tracking MCP tools."""

from fastmcp import FastMCP

from worksection_mcp.client import WorksectionClient


def register_activity_tools(mcp: FastMCP, client: WorksectionClient) -> None:
    """Register activity and event tracking tools with the MCP server."""

    @mcp.tool()
    async def get_activity_log(
        project_id: str | None = None,
        period: str | None = None,
        filter: str | None = None,
    ) -> dict:
        """Get activity/event log with flexible filtering.

        Args:
            project_id: Filter by project (optional)
            period: Time period for events (optional). Format:
                - Minutes: 1m to 360m (e.g., "120m" for 2 hours)
                - Hours: 1h to 72h (e.g., "24h" for 1 day)
                - Days: 1d to 30d (e.g., "7d" for 1 week)
            filter: Filter by event type (optional)

        Returns:
            Activity log entries:
            - events: List of activity events
            - Each event has: type, user, task/project, date, description
        """
        return await client.get_events(
            project_id=project_id,
            period=period,
            filter=filter,
        )

    @mcp.tool()
    async def get_recent_activity(period: str = "7d") -> dict:
        """Get recent activity across all projects.

        Args:
            period: Time period for events (default: "7d" for 7 days).
                Format: 1m-360m (minutes), 1h-72h (hours), 1d-30d (days)

        Returns:
            Recent activity:
            - events: List of recent events
            - Sorted by date (newest first)
        """
        return await client.get_events(period=period)

    @mcp.tool()
    async def get_project_activity(
        project_id: str,
        period: str | None = None,
    ) -> dict:
        """Get activity log for a specific project.

        Args:
            project_id: The project ID
            period: Time period for events (optional). Format:
                - Minutes: 1m to 360m (e.g., "120m" for 2 hours)
                - Hours: 1h to 72h (e.g., "24h" for 1 day)
                - Days: 1d to 30d (e.g., "7d" for 1 week)

        Returns:
            Project activity:
            - project_id: Project ID
            - events: Activity events
            - event_types: Count by event type
        """
        events_data = await client.get_events(
            project_id=project_id,
            period=period,
        )

        # Count by event type
        event_types = {}
        if isinstance(events_data, dict) and "data" in events_data:
            for event in events_data["data"]:
                event_type = event.get("type", "unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "project_id": project_id,
            "period": period,
            "events": events_data,
            "event_types": event_types,
        }

    @mcp.tool()
    async def get_user_activity(
        user_id: str,
        period: str | None = None,
    ) -> dict:
        """Get activity log for a specific user.

        Note: The Worksection get_events API filters by project, not by user.
        This function gets all events for the period and filters client-side.

        Args:
            user_id: The user ID
            period: Time period for events (optional). Format:
                - Minutes: 1m to 360m (e.g., "120m" for 2 hours)
                - Hours: 1h to 72h (e.g., "24h" for 1 day)
                - Days: 1d to 30d (e.g., "7d" for 1 week)

        Returns:
            User activity:
            - user_id: User ID
            - events: Activity events by this user
            - projects_touched: Projects this user interacted with
        """
        events_data = await client.get_events(period=period)

        # Filter by user and find unique projects
        user_events = []
        projects_touched = {}

        if isinstance(events_data, dict) and "data" in events_data:
            for event in events_data["data"]:
                # Check if this event was by the specified user
                # API returns user info in "user_from" field
                event_user = event.get("user_from", {})
                if str(event_user.get("id")) == str(user_id):
                    user_events.append(event)

                    project = event.get("project", {})
                    if project:
                        proj_id = project.get("id")
                        if proj_id and proj_id not in projects_touched:
                            projects_touched[proj_id] = {
                                "name": project.get("name"),
                                "event_count": 0,
                            }
                        if proj_id:
                            projects_touched[proj_id]["event_count"] += 1

        return {
            "user_id": user_id,
            "period": period,
            "events": {"data": user_events},
            "projects_touched": projects_touched,
        }
