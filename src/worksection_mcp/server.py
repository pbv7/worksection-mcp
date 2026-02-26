"""Worksection MCP Server - Main entry point."""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from worksection_mcp.auth import OAuth2Manager
from worksection_mcp.cache import FileCache
from worksection_mcp.client import WorksectionClient
from worksection_mcp.config import Settings, get_settings
from worksection_mcp.resources import register_file_resources
from worksection_mcp.tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


# Global instances (initialized in lifespan)
_oauth: OAuth2Manager | None = None
_client: WorksectionClient | None = None
_file_cache: FileCache | None = None


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        settings: Optional settings override (uses get_settings() if None)

    Returns:
        Configured FastMCP server instance
    """
    global _oauth, _client, _file_cache

    if settings is None:
        settings = get_settings()

    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, settings.log_level))

    # Ensure directories exist
    settings.ensure_directories()

    # Validate external resources
    logger.info("Validating external resources...")
    validation_results = settings.validate_external_resources()
    has_errors = False
    for key, result in validation_results.items():
        if result.startswith("✗"):
            logger.error(f"{key}: {result}")
            has_errors = True
        else:
            logger.debug(f"{key}: {result}")

    if has_errors:
        logger.warning("Some external resource checks failed. Server may not function correctly.")

    # Initialize OAuth2 manager
    _oauth = OAuth2Manager(settings)

    # Initialize Worksection client
    _client = WorksectionClient(_oauth, settings)

    # Initialize file cache
    _file_cache = FileCache(
        cache_path=settings.file_cache_path,
        max_file_size_bytes=settings.max_file_size_bytes,
        retention_hours=settings.file_cache_retention_hours,
    )

    # Define lifespan context manager for FastMCP 2.0
    @asynccontextmanager
    async def lifespan(_mcp: FastMCP):
        """Handle server startup and shutdown."""
        # Startup
        logger.info("Worksection MCP server starting...")
        logger.info(f"Account: {settings.worksection_account_url}")
        logger.info(f"API URL: {settings.api_base_url}")
        logger.info(f"Transport: {settings.mcp_transport}")

        try:
            if _oauth is None or _client is None:
                raise RuntimeError("Server dependencies are not initialized")
            # Ensure we have valid authentication
            await _oauth.ensure_authenticated()
            user_info = await _client.me()
            logger.info(f"Authenticated as: {user_info}")
            logger.info("Worksection MCP server ready!")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

        yield

        # Shutdown
        logger.info("Worksection MCP server shutting down...")

        # Clean up resources
        if _client:
            try:
                await _client.close()
            except asyncio.CancelledError:
                logger.debug("Shutdown cancelled while closing Worksection client")
            except Exception:
                logger.exception("Error while closing Worksection client")
        if _file_cache:
            try:
                await _file_cache.close()
            except asyncio.CancelledError:
                logger.debug("Shutdown cancelled while closing file cache")
            except Exception:
                logger.exception("Error while closing file cache")

        logger.info("Worksection MCP server stopped")

    # Create FastMCP server with lifespan
    mcp = FastMCP(
        name=settings.mcp_server_name,
        instructions="""
Worksection MCP Server - Comprehensive read-only access to Worksection project management.

This server provides comprehensive tools for accessing:
- Projects and folders
- Tasks with comments and attachments
- Time tracking and costs
- Team members and contacts
- Tags and analytics
- Activity logs

Image attachments can be accessed via MCP resources for Claude vision analysis.

Rate limited to 1 request/second per Worksection API limits.
        """.strip(),
        lifespan=lifespan,
    )

    if _oauth is None or _client is None or _file_cache is None:
        raise RuntimeError("Server dependencies are not initialized")

    # Register all tools
    register_all_tools(mcp, _client, _oauth, _file_cache)

    # Register file resources
    register_file_resources(mcp, _client, _file_cache)

    return mcp


# Lazy server instance
_mcp: FastMCP | None = None


def get_mcp() -> FastMCP:
    """Get or create the MCP server instance."""
    global _mcp
    if _mcp is None:
        _mcp = create_server()
    return _mcp


# Expose mcp via get_mcp() for backwards compatibility
mcp = None  # Will be set lazily when get_mcp() is called


def main():
    """Main entry point for the MCP server."""
    # Restrict permissions on all runtime-created files (tokens, keys, certs, cache).
    # Files: 600 (-rw-------), directories: 700 (drwx------).
    os.umask(0o077)

    settings = get_settings()
    server = create_server(settings)

    logger.info("Starting Worksection MCP server...")
    logger.info(f"Transport: {settings.mcp_transport}")
    logger.info(f"Port: {settings.mcp_server_port}")

    try:
        if settings.mcp_transport == "stdio":
            # Run with stdio transport (for local MCP clients)
            server.run(transport="stdio")
        elif settings.mcp_transport == "streamable-http":
            # Run with streamable HTTP transport (recommended network mode)
            server.run(
                transport="streamable-http",
                host=settings.mcp_server_host,
                port=settings.mcp_server_port,
                uvicorn_config={"timeout_graceful_shutdown": 5},
            )
        else:
            raise ValueError(f"Unsupported transport: {settings.mcp_transport}")
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user (Ctrl+C)")


if __name__ == "__main__":
    main()
