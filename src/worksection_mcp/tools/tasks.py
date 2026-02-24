"""Task-related MCP tools."""

import logging
from typing import Literal

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar

logger = logging.getLogger(__name__)


def register_task_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register task-related tools with the MCP server."""

    @mcp.tool()
    async def get_all_tasks(
        status_filter: Literal["active", "done", "all"] | None = None,
        extra: str | None = None,
    ) -> dict:
        """Get all tasks across all projects.

        Args:
            status_filter: Filter tasks by status:
                - active: Only incomplete tasks (default)
                - done: Only completed tasks
                - all: All tasks
            extra: Additional data to include. Valid values:
                text, files, comments, relations, subtasks, subscribers.
                Example: 'text' or 'text,files' for multiple.

        Returns:
            List of tasks with their details:
            - id, name, status, priority
            - project: Parent project info
            - user_from, user_to: Creator and assignee
            - dates: Creation, start, end, deadline
        """
        return await client.get_all_tasks(status_filter=status_filter, extra=extra)

    @mcp.tool()
    async def get_tasks(
        project_id: str,
        status_filter: Literal["active", "done", "all"] | None = None,
        extra: str | None = None,
    ) -> dict:
        """Get tasks for a specific project.

        Note: The Worksection API has a known issue where status_filter='done'
        combined with project_id may return incomplete results. When this
        combination is used, the tool fetches all tasks and filters client-side.

        Args:
            project_id: The project ID to get tasks from
            status_filter: Filter by status (active, done, all)
            extra: Additional data to include. Valid values:
                text, files, comments, relations, subtasks, subscribers.

        Returns:
            List of tasks in the specified project
        """
        # Workaround: status_filter='done' + project_id returns incomplete results
        if status_filter == "done":
            logger.warning(
                "Using client-side filtering for status_filter='done' + project_id=%s "
                "(known API compatibility issue)",
                project_id,
            )
            result = await client.get_tasks(project_id=project_id, status_filter="all", extra=extra)
            if isinstance(result, dict) and "data" in result:
                result["data"] = [
                    t for t in result["data"] if t.get("status") in ("done", "closed", "completed")
                ]
            return result

        return await client.get_tasks(
            project_id=project_id, status_filter=status_filter, extra=extra
        )

    @mcp.tool()
    async def get_task(
        task_id: str,
        extra: str | None = None,
    ) -> dict:
        """Get detailed information about a specific task.

        Args:
            task_id: The unique identifier of the task
            extra: Additional data to include. Valid values:
                text, files, comments, relations, subtasks, subscribers.
                Example: 'text' or 'text,files' for multiple.

        Returns:
            Complete task details including:
            - Basic info: id, name, status, priority
            - People: user_from (creator), user_to (assignee)
            - Dates: date_added, date_start, date_end, deadline
            - Project: parent project information
            - Extra data if requested (text, files, comments, etc.)
        """
        return await client.get_task(task_id=task_id, extra=extra)

    @mcp.tool()
    async def search_tasks(
        query: str | None = None,
        filter_query: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        assignee_email: str | None = None,
        author_email: str | None = None,
        status: Literal["active", "done"] | None = None,
        extra: str | None = None,
        max_results: int | None = 100,
    ) -> dict:
        """Search for tasks using name search or raw query syntax.

        Provide 'query' for simple name search, or 'filter_query' for advanced
        Worksection query syntax. filter_query takes precedence when both provided.

        Args:
            query: Simple text to search for in task names
            filter_query: Raw Worksection query, e.g. "name has 'Report' and dateend < '2024-06-01'".
                Fields: name, dateadd, datestart, dateend, dateclose.
                Operators: =, has, >, <, >=, <=, !=, in. Logic: and, or.
            project_id: Project ID to scope the search
            task_id: Task ID to scope the search
            assignee_email: Filter by assignee email
            author_email: Filter by task author email
            status: Filter by task state (active=incomplete, done=completed)
            extra: Additional data to include (text, html, files)
            max_results: Maximum number of results to return (default 100).
                None = no truncation. Must be positive if set.

        Returns:
            Search results with truncation metadata:
            - status, data: API response (data truncated to max_results)
            - total_count, returned_count, truncated: Truncation metadata
        """
        if max_results is not None and max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        if filter_query:
            search_filter = filter_query
        elif query:
            search_filter = f"name has '{query}'"
        else:
            search_filter = None

        result = await client.search_tasks(
            search_query=search_filter,
            project_id=project_id,
            task_id=task_id,
            email_user_from=author_email,
            email_user_to=assignee_email,
            status=status,
            extra=extra,
        )

        # Apply truncation if max_results is set
        if isinstance(result, dict) and "data" in result:
            data = result["data"]
            total = len(data) if isinstance(data, list) else 0
            if max_results is not None and isinstance(data, list):
                truncated_data = data[:max_results]
                result["data"] = truncated_data
                result["total_count"] = total
                result["returned_count"] = len(truncated_data)
                result["truncated"] = total > max_results
            else:
                result["total_count"] = total
                result["returned_count"] = total
                result["truncated"] = False

        return result

    @mcp.tool()
    async def get_task_subtasks(task_id: str) -> dict:
        """Get subtasks of a parent task.

        Args:
            task_id: The parent task ID

        Returns:
            Task details with subtasks list included:
            - subtasks: Array of subtask objects
            - Each subtask has: id, name, status, assignee
        """
        return await client.get_task(task_id=task_id, extra="subtasks")

    @mcp.tool()
    async def get_task_relations(task_id: str) -> dict:
        """Get related/dependent tasks.

        Args:
            task_id: The task ID

        Returns:
            Task details with relations included:
            - relations: Array of related task objects
            - Includes blocking and blocked-by relationships
        """
        return await client.get_task(task_id=task_id, extra="relations")

    @mcp.tool()
    async def get_task_subscribers(task_id: str) -> dict:
        """Get users subscribed/watching a task.

        Args:
            task_id: The task ID

        Returns:
            Task details with subscribers list:
            - subscribers: Array of user objects watching this task
        """
        return await client.get_task(task_id=task_id, extra="subscribers")
