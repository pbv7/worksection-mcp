"""System and account MCP tools."""

from fastmcp import FastMCP

from worksection_mcp.client import WorksectionClient
from worksection_mcp.auth import OAuth2Manager


def register_system_tools(
    mcp: FastMCP, client: WorksectionClient, oauth: OAuth2Manager | None = None
) -> None:
    """Register system and account tools with the MCP server."""

    @mcp.tool()
    async def get_account_info() -> dict:
        """Get information about the Worksection account.

        Returns account information derived from the current user's data,
        as the Worksection API doesn't provide a dedicated account endpoint.

        Returns:
            Account information:
            - account_url: Worksection account URL
            - user: Current user info (name, role, department)
            - authenticated: Whether authenticated successfully
        """
        # Get user info which includes account details
        user_info = await client.me()

        return {
            "account_url": client.settings.worksection_account_url,
            "user": user_info,
            "authenticated": True if user_info else False,
        }

    @mcp.tool()
    async def health_check() -> dict:
        """Check the health status of the MCP server.

        Verifies:
        - OAuth token validity
        - API connectivity
        - Current user authentication

        Returns:
            Health status:
            - status: 'healthy' or 'unhealthy'
            - token_valid: Whether OAuth token is valid
            - api_reachable: Whether API is reachable
            - user: Current authenticated user info
        """
        status = "healthy"
        token_valid = False
        api_reachable = False
        user_info = None
        error = None

        try:
            # Check token validity
            if oauth:
                token = await oauth.get_valid_token()
                token_valid = token is not None

            # Check API connectivity by getting current user
            user_info = await client.me()
            api_reachable = True

        except Exception as e:
            status = "unhealthy"
            error = str(e)

        return {
            "status": status,
            "token_valid": token_valid,
            "api_reachable": api_reachable,
            "user": user_info,
            "error": error,
        }

    @mcp.tool()
    async def get_current_user_info() -> dict:
        """Get comprehensive info about the authenticated user.

        This combines OAuth user info with Worksection account data.

        Returns:
            Current user information:
            - id: User ID
            - email: Email address
            - name: Full name
            - account_url: Worksection account URL
            - permissions: User permissions/role
        """
        # Get basic info from OAuth resource endpoint
        if oauth:
            oauth_info = await oauth.get_user_info()
        else:
            oauth_info = {}

        # Get detailed info from API
        api_info = await client.me()

        return {
            "oauth_info": oauth_info,
            "api_info": api_info,
        }

    @mcp.tool()
    async def get_api_status() -> dict:
        """Get API status and rate limit information.

        Returns:
            API status:
            - api_base_url: Base URL for API requests
            - account_url: Worksection account URL
            - rate_limit: Current rate limit settings
            - max_results: Maximum results per response
            - api_reachable: Whether API is responding
        """
        # Test API connectivity
        api_reachable = False
        try:
            await client.me()
            api_reachable = True
        except Exception:
            pass

        return {
            "api_base_url": client.settings.api_base_url,
            "account_url": client.settings.worksection_account_url,
            "rate_limit": "1 request/second",
            "max_results": "10,000 items per response",
            "api_reachable": api_reachable,
        }
