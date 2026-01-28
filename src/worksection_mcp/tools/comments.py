"""Comment-related MCP tools."""

from fastmcp import FastMCP

from worksection_mcp.client import WorksectionClient


def register_comment_tools(mcp: FastMCP, client: WorksectionClient) -> None:
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
        """Get the full discussion thread for a task.

        This returns all comments with their attached files,
        useful for understanding the full context of a task.

        Args:
            task_id: The task ID

        Returns:
            Task details along with complete comment thread:
            - task: Basic task information
            - comments: All comments with files
            - Total comment count
        """
        task_data = await client.get_task(task_id=task_id, extra="text")
        comments_data = await client.get_comments(task_id=task_id, extra="files")

        return {
            "task_id": task_id,
            "task": task_data,
            "comments": comments_data.get("data", []) if isinstance(comments_data, dict) else [],
            "comment_count": len(comments_data.get("data", [])) if isinstance(comments_data, dict) else 0,
        }

    @mcp.tool()
    async def get_comments_with_images(task_id: str) -> dict:
        """Get comments that have image attachments.

        Useful for finding screenshots, mockups, and visual content
        attached to task discussions.

        Args:
            task_id: The task ID

        Returns:
            Comments filtered to only those with image attachments:
            - comments: List of comments with images
            - Each comment includes file metadata (id, name, type)
        """
        comments_data = await client.get_comments(task_id=task_id, extra="files")

        # Filter to comments with image files
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
        comments_with_images = []

        if isinstance(comments_data, dict) and "data" in comments_data:
            for comment in comments_data["data"]:
                files = comment.get("files", [])
                image_files = [
                    f for f in files
                    if any(f.get("name", "").lower().endswith(ext) for ext in image_extensions)
                ]
                if image_files:
                    comments_with_images.append({
                        **comment,
                        "files": image_files,
                        "image_count": len(image_files),
                    })

        return {
            "task_id": task_id,
            "comments_with_images": comments_with_images,
            "total_images": sum(c["image_count"] for c in comments_with_images),
        }
