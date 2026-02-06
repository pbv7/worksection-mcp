"""
Worksection MCP Server

A multi-tenant MCP server for Worksection with 46+ read-only tools
for comprehensive data access and reporting.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("worksection-mcp")
except PackageNotFoundError:
    # Source tree execution before package install.
    __version__ = "0.0.0"


def main():
    """Main entry point for the MCP server."""
    from worksection_mcp.server import main as _main

    return _main()


def get_mcp():
    """Get the MCP server instance (lazy loading)."""
    from worksection_mcp.server import mcp

    return mcp


__all__ = ["__version__", "get_mcp", "main"]
