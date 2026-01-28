"""Task-related MCP tools."""

from typing import Literal

from fastmcp import FastMCP

from worksection_mcp.client import WorksectionClient


def register_task_tools(mcp: FastMCP, client: WorksectionClient) -> None:
    """Register task-related tools with the MCP server."""

    @mcp.tool()
    async def get_all_tasks(
        filter: Literal["active", "done", "all"] | None = None,
        extra: Literal["text", "files", "comments", "relations", "subtasks", "subscribers"] | None = None,
    ) -> dict:
        """Get all tasks across all projects.

        Args:
            filter: Filter tasks by status:
                - active: Only incomplete tasks (default)
                - done: Only completed tasks
                - all: All tasks
            extra: Additional data to include:
                - text: Full task description
                - files: Attached files
                - comments: Task comments
                - relations: Related/dependent tasks
                - subtasks: Subtask list
                - subscribers: Task watchers

        Returns:
            List of tasks with their details:
            - id, name, status, priority
            - project: Parent project info
            - user_from, user_to: Creator and assignee
            - dates: Creation, start, end, deadline
        """
        return await client.get_all_tasks(filter=filter, extra=extra)

    @mcp.tool()
    async def get_tasks(
        project_id: str,
        filter: Literal["active", "done", "all"] | None = None,
        extra: Literal["text", "files", "comments", "relations", "subtasks", "subscribers"] | None = None,
    ) -> dict:
        """Get tasks for a specific project.

        Args:
            project_id: The project ID to get tasks from
            filter: Filter by status (active, done, all)
            extra: Additional data to include

        Returns:
            List of tasks in the specified project
        """
        return await client.get_tasks(project_id=project_id, filter=filter, extra=extra)

    @mcp.tool()
    async def get_task(
        task_id: str,
        extra: Literal["text", "files", "comments", "relations", "subtasks", "subscribers"] | None = None,
    ) -> dict:
        """Get detailed information about a specific task.

        Args:
            task_id: The unique identifier of the task
            extra: Additional data to include

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
        query: str,
        project_id: str | None = None,
        assignee_email: str | None = None,
        author_email: str | None = None,
        status: Literal["active", "done"] | None = None,
        extra: Literal["text", "html", "files"] | None = None,
    ) -> dict:
        """Search for tasks by name.

        Uses Worksection's search query syntax to find tasks matching the query.

        Args:
            query: Text to search for in task names
            project_id: Project ID to scope the search (recommended for better results)
            assignee_email: Filter by assignee email
            author_email: Filter by task author email
            status: Filter by task state (active=incomplete, done=completed)
            extra: Additional data to include (text, html, files)

        Returns:
            List of tasks matching the search query
        """
        # Build the filter query - search by task name
        filter_query = f"name has '{query}'"

        return await client.search_tasks(
            filter=filter_query,
            project_id=project_id,
            email_user_from=author_email,
            email_user_to=assignee_email,
            status=status,
            extra=extra,
        )

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

    @mcp.tool()
    async def get_task_with_comments_and_files(task_id: str) -> dict:
        """Get task with all comments and file attachments.

        This is useful for generating reports that need the full context
        of a task including all discussion and attached screenshots.

        Args:
            task_id: The task ID

        Returns:
            Complete task with:
            - Task details
            - All comments with their content
            - All attached files with metadata
        """
        # Get task with both comments and files
        task_data = await client.get_task(task_id=task_id, extra="text")
        comments_data = await client.get_comments(task_id=task_id, extra="files")

        return {
            "status": "ok",
            "data": task_data.get("data") if isinstance(task_data, dict) else task_data,
            "task": task_data,
            "comments": comments_data.get("data", []) if isinstance(comments_data, dict) else [],
        }
