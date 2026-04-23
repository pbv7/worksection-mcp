"""MCP resources."""

from worksection_mcp.resources.files import register_file_resources
from worksection_mcp.resources.offload import register_large_response_resources

__all__ = ["register_file_resources", "register_large_response_resources"]
