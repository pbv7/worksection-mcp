"""Activity and event tracking MCP tools."""

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar
from worksection_mcp.utils.date_utils import validate_period


def register_activity_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register activity and event tracking tools with the MCP server."""

    @mcp.tool()
    async def get_activity_log(
        project_id: str | None = None,
        period: str = "7d",
        event_filter: str | None = None,
    ) -> dict:
        """Get activity/event log with flexible filtering.

        Use this to see recent changes across all projects or within a specific
        project. Returns an event-type breakdown for quick overview.

        Args:
            project_id: Filter by project (optional)
            period: Time period for events, e.g. '7d', '24h', '120m'.
                Minutes: 1m-360m, Hours: 1h-72h, Days: 1d-30d.
            event_filter: Filter by event type (optional)

        Returns:
            Activity log with event_types breakdown:
            - data: List of activity events
            - event_types: Count by event type
        """
        if not validate_period(period):
            return {
                "error": f"Invalid period format: '{period}'. "
                "Use Nm (1-360), Nh (1-72), or Nd (1-30).",
            }

        events_data = await client.get_events(
            project_id=project_id,
            period=period,
            event_filter=event_filter,
        )

        # Count by event type
        event_types: dict[str, int] = {}
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
        period: str = "7d",
    ) -> dict:
        """Get activity log for a specific user.

        Note: The Worksection get_events API filters by project, not by user.
        This function gets all events for the period and filters client-side.

        Args:
            user_id: The user ID
            period: Time period for events, e.g. '7d', '24h', '120m'.
                Minutes: 1m-360m, Hours: 1h-72h, Days: 1d-30d.

        Returns:
            User activity:
            - user_id: User ID
            - events: Activity events by this user
            - projects_touched: Projects this user interacted with
        """
        if not validate_period(period):
            return {
                "error": f"Invalid period format: '{period}'. "
                "Use Nm (1-360), Nh (1-72), or Nd (1-30).",
            }

        events_data = await client.get_events(period=period)

        # Filter by user and find unique projects
        user_events = []
        projects_touched: dict[str, dict] = {}

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
