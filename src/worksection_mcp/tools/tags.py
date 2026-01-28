"""Tag-related MCP tools (read-only)."""

from fastmcp import FastMCP

from worksection_mcp.client import WorksectionClient


def register_tag_tools(mcp: FastMCP, client: WorksectionClient) -> None:
    """Register tag-related tools with the MCP server."""

    # ==========================================================================
    # Task Tags (Read-only)
    # ==========================================================================

    @mcp.tool()
    async def get_task_tags(
        group: str | None = None,
        tag_type: str | None = None,
        access: str | None = None,
    ) -> dict:
        """Get available task tags (labels and statuses).

        Args:
            group: Filter by tag group name or ID (optional)
            tag_type: Filter by type - 'status' or 'label' (optional)
            access: Filter by visibility - 'public' or 'private' (optional)

        Returns:
            List of available task tags with their groups:
            - id: Tag ID
            - title: Tag name
            - group: Tag group info (title, id, type, access)
        """
        return await client.get_task_tags(group=group, tag_type=tag_type, access=access)

    @mcp.tool()
    async def get_task_tag_groups(
        tag_type: str | None = None,
        access: str | None = None,
    ) -> dict:
        """Get task tag groups.

        Args:
            tag_type: Filter by type - 'status' or 'label' (optional)
            access: Filter by visibility - 'public' or 'private' (optional)

        Returns:
            List of tag groups:
            - id: Group ID
            - title: Group name
            - type: 'status' or 'label'
            - access: 'public' or 'private'
        """
        return await client.get_task_tag_groups(tag_type=tag_type, access=access)

    # ==========================================================================
    # Project Tags (Read-only)
    # ==========================================================================

    @mcp.tool()
    async def get_project_tags(
        group: str | None = None,
        tag_type: str | None = None,
        access: str | None = None,
    ) -> dict:
        """Get available project tags.

        Args:
            group: Filter by tag group name or ID (optional)
            tag_type: Filter by type - 'status' or 'label' (optional)
            access: Filter by visibility - 'public' or 'private' (optional)

        Returns:
            List of available project tags with their groups
        """
        return await client.get_project_tags(group=group, tag_type=tag_type, access=access)

    @mcp.tool()
    async def get_project_tag_groups(
        tag_type: str | None = None,
        access: str | None = None,
    ) -> dict:
        """Get project tag groups.

        Args:
            tag_type: Filter by type - 'status' or 'label' (optional)
            access: Filter by visibility - 'public' or 'private' (optional)

        Returns:
            List of project tag groups
        """
        return await client.get_project_tag_groups(tag_type=tag_type, access=access)

    # ==========================================================================
    # Task Tag Lookup (uses get_task which includes tags)
    # ==========================================================================

    @mcp.tool()
    async def get_task_with_tags(task_id: str) -> dict:
        """Get a task with its tags.

        The Worksection API only returns tags when fetching individual tasks.
        Use this to check what tags are assigned to a specific task.

        Args:
            task_id: The task ID

        Returns:
            Task data including:
            - tags: Dict of {tag_id: tag_name} for assigned tags
            - tag_names: List of tag names for convenience
        """
        result = await client.get_task(task_id=task_id)

        if result.get("status") == "ok" and "data" in result:
            task_data = result["data"]
            tags = task_data.get("tags", {})
            return {
                "status": "ok",
                "task_id": task_id,
                "task_name": task_data.get("name"),
                "tags": tags,
                "tag_names": list(tags.values()) if isinstance(tags, dict) else [],
            }

        return result

    @mcp.tool()
    async def search_tasks_by_tag(
        tag: str,
        project_id: str,
    ) -> dict:
        """Find tasks with a specific tag in a project.

        Args:
            tag: The tag name to search for (case-insensitive)
            project_id: Project ID to search in

        Returns:
            - tag: The searched tag
            - tasks: List of matching tasks
            - count: Number of matches found
        """
        # Get all tasks from project with tags included
        # The 'extra' parameter with 'tags' value tells API to include task tags
        tasks_data = await client.get_tasks(project_id=project_id, filter="all", extra="tags")

        if not isinstance(tasks_data, dict) or "data" not in tasks_data:
            return {
                "tag": tag,
                "tasks": [],
                "count": 0,
                "error": "Failed to get tasks",
            }

        filtered_tasks = []
        tag_lower = tag.lower()

        for task in tasks_data["data"]:
            task_tags = task.get("tags", {})

            # Tags are returned as {tag_id: tag_name} dict
            if isinstance(task_tags, dict):
                for tag_name in task_tags.values():
                    if isinstance(tag_name, str) and tag_name.lower() == tag_lower:
                        filtered_tasks.append(task)
                        break

        return {
            "tag": tag,
            "tasks": filtered_tasks,
            "count": len(filtered_tasks),
        }
