"""System and account MCP tools."""

import logging
from typing import Any, Protocol

from worksection_mcp.client import WorksectionClient
from worksection_mcp.client.api import WorksectionAPIError
from worksection_mcp.mcp_protocols import ToolRegistrar

logger = logging.getLogger(__name__)


class OAuthInfoProvider(Protocol):
    """Protocol for OAuth providers used by system tools."""

    async def get_valid_token(self) -> str:
        """Return a valid access token."""
        ...

    async def get_user_info(self) -> dict[str, Any]:
        """Return user info from OAuth resource endpoint."""
        ...


def register_system_tools(
    mcp: ToolRegistrar, client: WorksectionClient, oauth: OAuthInfoProvider | None = None
) -> None:
    """Register system and account tools with the MCP server."""

    @mcp.tool()
    async def health_check() -> dict:
        """Check the health status of the MCP server and API connectivity.

        Verifies OAuth token validity, API reachability, and returns
        useful connection metadata.

        Returns:
            Health status:
            - status: 'healthy' or 'unhealthy'
            - token_valid: Whether OAuth token is valid
            - api_reachable: Whether API is reachable
            - user: Current authenticated user info
            - api_base_url: Base URL for API requests
            - account_url: Worksection account URL
            - rate_limit: Rate limit info
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
            "api_base_url": client.settings.api_base_url,
            "account_url": client.settings.worksection_account_url,
            "rate_limit": "1 request/second (adaptive)",
            "error": error,
        }

    @mcp.tool()
    async def get_webhooks() -> dict:
        """List all configured webhooks for the Worksection account.

        Note: This endpoint requires the 'administrative' scope which must
        be manually added to WORKSECTION_SCOPES in your configuration.

        Returns:
            List of webhooks:
            - id: Webhook ID
            - url: Callback URL
            - events: Subscribed event types
        """
        try:
            return await client.get_webhooks()
        except WorksectionAPIError as e:
            error_msg = str(e)
            result: dict[str, Any] = {"status": "error", "error": error_msg}
            if "permissions" in error_msg.lower() or "administrative" in error_msg.lower():
                result["hint"] = (
                    "Add 'administrative' to WORKSECTION_SCOPES in your configuration "
                    "to use this endpoint."
                )
            return result
