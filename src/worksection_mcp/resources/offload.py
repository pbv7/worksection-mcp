"""MCP resources for large response offload previews."""

from worksection_mcp.large_response import LargeResponseStore
from worksection_mcp.mcp_protocols import ResourceRegistrar


def register_large_response_resources(
    mcp: ResourceRegistrar,
    store: LargeResponseStore,
) -> None:
    """Register resources for offloaded response previews.

    The resource intentionally returns only metadata plus a small preview. The
    full payload was offloaded because it is too large for MCP responses; use
    read_offloaded_response_text for bounded access to JSON/text payloads.
    """

    @mcp.resource("worksection://offload/{response_id}")
    async def get_offloaded_response(response_id: str) -> dict:
        """Get metadata and a small preview for an offloaded tool response."""
        return store.get_resource_preview(response_id)
