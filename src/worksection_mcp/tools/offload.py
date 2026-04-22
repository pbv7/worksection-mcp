"""MCP helper tools for offloaded large responses."""

from worksection_mcp.large_response import LargeResponseStore
from worksection_mcp.mcp_protocols import ToolRegistrar


def register_offload_tools(mcp: ToolRegistrar, store: LargeResponseStore) -> None:
    """Register helper tools for inspecting offloaded response files."""

    @mcp.tool()
    async def get_offloaded_response_info(response_id: str) -> dict:
        """Get metadata for an offloaded tool response.

        Args:
            response_id: The offloaded response ID returned in the offload envelope.

        Returns:
            Metadata including size, hash, MIME type, creation time, and resource URI.
        """
        return store.get_payload_metadata(response_id)

    @mcp.tool()
    async def read_offloaded_response_text(
        response_id: str,
        offset: int = 0,
        max_bytes: int | None = None,
    ) -> dict:
        """Read a bounded text slice from an offloaded JSON/text response.

        Args:
            response_id: The offloaded response ID returned in the offload envelope.
            offset: Byte offset to start reading from.
            max_bytes: Maximum raw bytes to read. Defaults to the configured cap.

        Returns:
            Text content slice and pagination metadata, or a compact error.
        """
        return store.read_text_slice(
            response_id=response_id,
            offset=offset,
            max_bytes=store.max_read_bytes if max_bytes is None else max_bytes,
        )
