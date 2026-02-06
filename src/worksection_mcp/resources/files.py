"""MCP resources for file access."""

import base64
import logging

from worksection_mcp.cache import FileCache
from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ResourceRegistrar

logger = logging.getLogger(__name__)


def register_file_resources(
    mcp: ResourceRegistrar, client: WorksectionClient, file_cache: FileCache
) -> None:
    """Register file resources with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: WorksectionClient instance
        file_cache: FileCache instance for caching downloaded files
    """

    @mcp.resource("worksection://file/{file_id}")
    async def get_file_resource(file_id: str) -> dict:
        """Get a Worksection file as an MCP resource.

        This resource allows Claude to directly access and analyze
        files (especially images) attached to tasks and comments.

        The file is downloaded from Worksection and cached locally.
        Subsequent requests for the same file will use the cache.

        Args:
            file_id: The Worksection file ID

        Returns:
            Resource with file content and metadata:
            - uri: The resource URI
            - name: File name (if available)
            - mimeType: MIME type of the file
            - blob: Base64-encoded file content for binary files
            - text: Text content for text files
        """
        # Check cache first
        cached = await file_cache.get(file_id)

        if cached:
            logger.debug(f"Serving file {file_id} from cache")
            content = cached.path.read_bytes()
            mime_type = cached.mime_type
        else:
            # Download from Worksection
            logger.debug(f"Downloading file {file_id} from Worksection")
            content = await client.download_file(file_id)

            # Cache the file
            await file_cache.save(file_id, content)
            cached = await file_cache.get(file_id)
            mime_type = cached.mime_type if cached else "application/octet-stream"

        # Determine if it's a text or binary file
        is_text = mime_type.startswith("text/") or mime_type in (
            "application/json",
            "application/xml",
            "application/javascript",
        )

        if is_text:
            try:
                text_content = content.decode("utf-8")
                return {
                    "uri": f"worksection://file/{file_id}",
                    "mimeType": mime_type,
                    "text": text_content,
                }
            except UnicodeDecodeError:
                # Fall back to binary
                pass

        # Return as binary (base64 encoded)
        return {
            "uri": f"worksection://file/{file_id}",
            "mimeType": mime_type,
            "blob": base64.b64encode(content).decode("utf-8"),
        }

    @mcp.resource("worksection://task/{task_id}/context")
    async def get_task_full_context(task_id: str) -> dict:
        """Get complete context for a task including all comments and attachments.

        This resource provides a comprehensive view of a task for report generation:
        - Task details and description
        - All comments in the discussion thread
        - List of all attached files (with URIs for access)
        - Image files are highlighted for Claude vision analysis

        Args:
            task_id: The Worksection task ID

        Returns:
            Complete task context:
            - task: Task details
            - comments: All comments with metadata
            - attachments: All files with access URIs
            - images: Image files ready for vision analysis
        """
        # Get task with text
        task_data = await client.get_task(task_id=task_id, extra="text")

        # Get task files
        task_with_files = await client.get_task(task_id=task_id, extra="files")
        # Files can be in response["data"]["files"] or response["files"]
        if isinstance(task_with_files, dict):
            data = task_with_files.get("data", task_with_files)
            task_files = data.get("files", [])
        else:
            task_files = []

        # Get comments with files
        comments_data = await client.get_comments(task_id=task_id, extra="files")
        comments = comments_data.get("data", []) if isinstance(comments_data, dict) else []

        # Collect all attachments
        all_attachments = []
        images = []

        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}

        # Task files
        for file in task_files:
            file_entry = {
                "id": file.get("id"),
                "name": file.get("name"),
                "uri": f"worksection://file/{file.get('id')}",
                "source": "task",
            }
            all_attachments.append(file_entry)

            name = file.get("name", "")
            if any(name.lower().endswith(ext) for ext in image_extensions):
                images.append(file_entry)

        # Comment files
        for comment in comments:
            for file in comment.get("files", []):
                file_entry = {
                    "id": file.get("id"),
                    "name": file.get("name"),
                    "uri": f"worksection://file/{file.get('id')}",
                    "source": "comment",
                    "comment_id": comment.get("id"),
                    "comment_preview": comment.get("text", "")[:100],
                }
                all_attachments.append(file_entry)

                name = file.get("name", "")
                if any(name.lower().endswith(ext) for ext in image_extensions):
                    images.append(file_entry)

        return {
            "uri": f"worksection://task/{task_id}/context",
            "mimeType": "application/json",
            "text": None,  # Will be JSON serialized
            "data": {
                "task": task_data,
                "comments": comments,
                "attachments": all_attachments,
                "images": images,
                "summary": {
                    "comment_count": len(comments),
                    "attachment_count": len(all_attachments),
                    "image_count": len(images),
                },
            },
        }

    @mcp.resource("worksection://cache/stats")
    async def get_cache_stats() -> dict:
        """Get file cache statistics.

        Returns information about the local file cache:
        - Number of cached files
        - Total cache size
        - Cache configuration

        Returns:
            Cache statistics
        """
        stats = await file_cache.get_cache_stats()
        return {
            "uri": "worksection://cache/stats",
            "mimeType": "application/json",
            "text": None,
            "data": stats,
        }
