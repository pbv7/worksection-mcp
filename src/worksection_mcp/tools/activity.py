"""Activity and event tracking MCP tools."""

import logging

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar
from worksection_mcp.utils.date_utils import validate_period
from worksection_mcp.utils.response_utils import truncate_to_size

logger = logging.getLogger(__name__)


def register_activity_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register activity and event tracking tools with the MCP server."""

    @mcp.tool()
    async def get_activity_log(
        project_id: str | None = None,
        period: str = "1d",
        event_filter: str | None = None,
        max_results: int | None = None,
    ) -> dict:
        """Get activity/event log with flexible filtering.

        Use this to see recent changes across all projects or within a specific
        project. Returns an event-type breakdown for quick overview.

        When max_results is None (default), returns as many events as safely fit
        under MCP response-size limits with automatic truncation. Set an explicit
        value to cap the result count.

        Args:
            project_id: Filter by project (optional)
            period: Time period for events, e.g. '1d', '24h', '120m'.
                Minutes: 1m-360m, Hours: 1h-72h, Days: 1d-30d (default: 1d)
            event_filter: Filter by event type, e.g. 'task', 'project', 'comment' (optional).
                Applied client-side on the object type field.
            max_results: Maximum number of events to return. None = auto-size
                (as many as fit under MCP limits). Must be positive if set.

        Returns:
            Activity log with event_types breakdown:
            - events: List of activity events
            - total_count: Total number of events matching filters
            - returned_count: Number of events returned
            - truncated: Whether results were truncated
            - truncation_reason: 'none', 'max_results', 'size_cap', or 'both'
            - event_types: Count by event type (based on all filtered events)
        """
        if not validate_period(period):
            return {
                "error": f"Invalid period format: '{period}'. "
                "Use Nm (1-360), Nh (1-72), or Nd (1-30).",
            }

        if max_results is not None and max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        events_data = await client.get_events(
            project_id=project_id,
            period=period,
        )

        # Extract events list
        events_list: list = []

        if isinstance(events_data, dict) and "data" in events_data:
            events_list = events_data["data"]

        # Client-side event_filter on object.type
        if event_filter:
            filter_lower = event_filter.lower()
            events_list = [
                e
                for e in events_list
                if e.get("object", {}).get("type", "unknown").lower() == filter_lower
            ]

        # Count by event type (on full filtered set, before truncation)
        event_types: dict[str, int] = {}
        for event in events_list:
            event_type = event.get("object", {}).get("type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        total_count = len(events_list)
        truncation_reason = "none"

        # Apply max_results truncation
        if max_results is not None and len(events_list) > max_results:
            events_list = events_list[:max_results]
            truncation_reason = "max_results"

        # Apply size-cap safeguard
        events_list, size_truncated = truncate_to_size(events_list)
        if size_truncated:
            truncation_reason = "both" if truncation_reason == "max_results" else "size_cap"

        return {
            "project_id": project_id,
            "period": period,
            "events": events_list,
            "total_count": total_count,
            "returned_count": len(events_list),
            "truncated": truncation_reason != "none",
            "truncation_reason": truncation_reason,
            "event_types": event_types,
        }

    @mcp.tool()
    async def get_user_activity(
        user_id: str,
        period: str = "1d",
        max_results: int | None = None,
    ) -> dict:
        """Get activity log for a specific user.

        Note: The Worksection get_events API filters by project, not by user.
        This function gets all events for the period and filters client-side.

        When max_results is None (default), returns as many events as safely fit
        under MCP response-size limits with automatic truncation.

        Args:
            user_id: The user ID
            period: Time period for events, e.g. '1d', '24h', '120m'.
                Minutes: 1m-360m, Hours: 1h-72h, Days: 1d-30d (default: 1d)
            max_results: Maximum number of events to return. None = auto-size.
                Must be positive if set.

        Returns:
            User activity:
            - user_id: User ID
            - events: Activity events by this user
            - total_count: Total number of events by this user
            - returned_count: Number of events returned
            - truncated: Whether results were truncated
            - truncation_reason: 'none', 'max_results', 'size_cap', or 'both'
            - projects_touched: Projects this user interacted with
        """
        if not validate_period(period):
            return {
                "error": f"Invalid period format: '{period}'. "
                "Use Nm (1-360), Nh (1-72), or Nd (1-30).",
            }

        if max_results is not None and max_results <= 0:
            raise ValueError("max_results must be a positive integer")

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

        total_count = len(user_events)
        truncation_reason = "none"

        # Apply max_results truncation
        if max_results is not None and len(user_events) > max_results:
            user_events = user_events[:max_results]
            truncation_reason = "max_results"

        # Apply size-cap safeguard
        user_events, size_truncated = truncate_to_size(user_events)
        if size_truncated:
            truncation_reason = "both" if truncation_reason == "max_results" else "size_cap"

        return {
            "user_id": user_id,
            "period": period,
            "events": user_events,
            "total_count": total_count,
            "returned_count": len(user_events),
            "truncated": truncation_reason != "none",
            "truncation_reason": truncation_reason,
            "projects_touched": projects_touched,
        }
