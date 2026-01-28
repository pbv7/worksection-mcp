"""MCP tools for Worksection API."""

from worksection_mcp.tools.projects import register_project_tools
from worksection_mcp.tools.tasks import register_task_tools
from worksection_mcp.tools.comments import register_comment_tools
from worksection_mcp.tools.files import register_file_tools
from worksection_mcp.tools.timers import register_timer_tools
from worksection_mcp.tools.users import register_user_tools
from worksection_mcp.tools.tags import register_tag_tools
from worksection_mcp.tools.analytics import register_analytics_tools
from worksection_mcp.tools.activity import register_activity_tools
from worksection_mcp.tools.system import register_system_tools


def register_all_tools(mcp, client, oauth=None, file_cache=None):
    """Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
        client: WorksectionClient instance
        oauth: OAuth2Manager instance (optional, for system tools)
        file_cache: FileCache instance (optional, for file tools)
    """
    register_project_tools(mcp, client)
    register_task_tools(mcp, client)
    register_comment_tools(mcp, client)
    register_file_tools(mcp, client, file_cache)
    register_timer_tools(mcp, client)
    register_user_tools(mcp, client)
    register_tag_tools(mcp, client)
    register_analytics_tools(mcp, client)
    register_activity_tools(mcp, client)
    register_system_tools(mcp, client, oauth)


__all__ = ["register_all_tools"]
