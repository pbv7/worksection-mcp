"""Comment-related MCP tools."""

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar


def register_comment_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register comment-related tools with the MCP server."""

    @mcp.tool()
    async def get_comments(
        task_id: str,
        include_files: bool = False,
    ) -> dict:
        """Get all comments for a task.

        Args:
            task_id: The task ID to get comments for
            include_files: Whether to include file attachments in response

        Returns:
            List of comments with:
            - id: Comment ID
            - text: Comment content
            - date_added: When comment was posted
            - user_from: Who posted the comment
            - files: Attached files (if include_files=True)
        """
        extra = "files" if include_files else None
        return await client.get_comments(task_id=task_id, extra=extra)

    @mcp.tool()
    async def get_task_discussion(task_id: str) -> dict:
        """Get the full discussion thread for a task including comments and files.

        Use this to get complete task context: description text, all comments
        with their file attachments. Replaces the need to call get_task + get_comments
        separately.

        Args:
            task_id: The task ID

        Returns:
            Task details along with complete comment thread:
            - task: Task information with description text
            - comments: All comments with file attachments
            - comment_count: Total number of comments
        """
        task_data = await client.get_task(task_id=task_id, extra="text")
        comments_data = await client.get_comments(task_id=task_id, extra="files")

        return {
            "task_id": task_id,
            "task": task_data,
            "comments": comments_data.get("data", []) if isinstance(comments_data, dict) else [],
            "comment_count": len(comments_data.get("data", []))
            if isinstance(comments_data, dict)
            else 0,
        }
