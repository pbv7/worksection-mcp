"""OAuth2 authentication manager for Worksection."""

import logging
import secrets
import webbrowser
from urllib.parse import urlencode

import httpx

from worksection_mcp.auth.callback import CallbackServer
from worksection_mcp.auth.tokens import TokenStorage
from worksection_mcp.config import Settings

logger = logging.getLogger(__name__)


class OAuth2Error(Exception):
    """OAuth2 authentication error."""

    pass


class OAuth2Manager:
    """Manages OAuth2 authentication flow for Worksection."""

    def __init__(self, settings: Settings):
        """Initialize OAuth2 manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.token_storage = TokenStorage(
            storage_path=settings.token_storage_path,
            encryption_key=settings.token_encryption_key,
        )
        self._callback_server: CallbackServer | None = None
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def _build_authorize_url(self, state: str) -> str:
        """Build OAuth2 authorization URL.

        Args:
            state: CSRF state token

        Returns:
            Full authorization URL
        """
        params = {
            "client_id": self.settings.worksection_client_id,
            "redirect_uri": self.settings.worksection_redirect_uri,
            "response_type": "code",
            "scope": self.settings.worksection_scopes,
            "state": state,
        }
        base_url = f"{self.settings.oauth2_base_url}/oauth2/authorize"
        return f"{base_url}?{urlencode(params)}"

    async def _exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response

        Raises:
            OAuth2Error: If token exchange fails
        """
        client = await self._get_http_client()

        data = {
            "client_id": self.settings.worksection_client_id,
            "client_secret": self.settings.worksection_client_secret,
            "redirect_uri": self.settings.worksection_redirect_uri,
            "grant_type": "authorization_code",
            "code": code,
        }

        url = f"{self.settings.oauth2_base_url}/oauth2/token"
        logger.debug(f"Exchanging code at {url}")

        response = await client.post(url, data=data)

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error = error_data.get("error", "unknown_error")
            error_desc = error_data.get("error_description", response.text)
            raise OAuth2Error(f"Token exchange failed: {error} - {error_desc}")

        return response.json()

    async def _refresh_token(self) -> dict:
        """Refresh access token using refresh token.

        Returns:
            New token response

        Raises:
            OAuth2Error: If refresh fails
        """
        refresh_token = self.token_storage.get_refresh_token()
        if not refresh_token:
            raise OAuth2Error("No refresh token available")

        client = await self._get_http_client()

        data = {
            "client_id": self.settings.worksection_client_id,
            "client_secret": self.settings.worksection_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        url = f"{self.settings.oauth2_base_url}/oauth2/refresh"
        logger.debug("Refreshing access token")

        response = await client.post(url, data=data)
        response_data = response.json() if response.content else {}

        if response.status_code != 200:
            error = response_data.get("error", "unknown_error")
            error_desc = response_data.get("error_description", response.text)
            raise OAuth2Error(f"Token refresh failed: {error} - {error_desc}")

        # Validate response contains required fields (API may return 200 with error body)
        if "access_token" not in response_data:
            error = response_data.get("error", "invalid_response")
            error_desc = response_data.get("error_description", "No access_token in response")
            logger.warning(f"Token refresh response missing access_token: {response_data}")
            raise OAuth2Error(f"Token refresh failed: {error} - {error_desc}")

        return response_data

    async def authenticate(self) -> None:
        """Run interactive OAuth2 authorization flow.

        This starts a callback server, opens the browser for user consent,
        and exchanges the authorization code for tokens.

        Raises:
            OAuth2Error: If authentication fails
        """
        state = secrets.token_urlsafe(32)

        # Initialize SSL if enabled
        ssl_context = None
        if self.settings.oauth_callback_use_ssl:
            from worksection_mcp.auth.ssl_utils import create_ssl_context, ensure_ssl_cert

            ensure_ssl_cert(
                self.settings.oauth_ssl_cert_path,
                self.settings.oauth_ssl_key_path,
                self.settings.oauth_ssl_cert_days,
                self.settings.oauth_callback_host,
            )
            ssl_context = create_ssl_context(
                self.settings.oauth_ssl_cert_path,
                self.settings.oauth_ssl_key_path,
            )

        # Start callback server
        self._callback_server = CallbackServer(
            host=self.settings.oauth_callback_host,
            port=self.settings.oauth_callback_port,
            ssl_context=ssl_context,
        )
        self._callback_server.start()

        try:
            # Build authorization URL
            auth_url = self._build_authorize_url(state)
            logger.info(f"Authorization URL: {auth_url}")

            # Open browser for user consent
            if self.settings.oauth_auto_open_browser:
                logger.info("Opening browser for authorization...")
                webbrowser.open(auth_url)
            else:
                logger.warning("Please open this URL in your browser:\n%s", auth_url)

            # Wait for callback
            logger.info("Waiting for authorization callback...")
            code, returned_state = await self._callback_server.wait_for_callback(
                timeout_seconds=300
            )

            # Verify state
            if returned_state != state:
                raise OAuth2Error("State mismatch - possible CSRF attack")

            # Exchange code for tokens
            logger.info("Exchanging authorization code for tokens...")
            token_response = await self._exchange_code(code)

            # Save tokens
            self.token_storage.save(token_response)
            logger.info("Authentication successful!")

        finally:
            # Stop callback server
            self._callback_server.stop()
            self._callback_server = None

    async def ensure_authenticated(self) -> None:
        """Ensure we have a valid access token, authenticating if needed.

        This method will:
        1. Check if we have a valid access token (local expiration check)
        2. If not, try to refresh using refresh token
        3. If refresh fails, run full authentication flow

        Raises:
            OAuth2Error: If authentication fails
        """
        # Check for valid access token (local expiration check with 5-min buffer)
        if self.token_storage.is_access_token_valid():
            logger.debug("Access token is valid")
            return

        # Try to refresh
        refresh_token = self.token_storage.get_refresh_token()
        if refresh_token:
            try:
                logger.info("Access token expired, attempting refresh...")
                token_response = await self._refresh_token()
                self.token_storage.save(token_response)
                logger.info("Token refreshed successfully")
                return
            except OAuth2Error as e:
                logger.warning(f"Token refresh failed: {e}")
                # Clear invalid tokens
                self.token_storage.delete()

        # Need full authentication
        logger.info("No valid tokens, starting authentication flow...")
        await self.authenticate()

    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if needed.

        Returns:
            Valid access token

        Raises:
            OAuth2Error: If no valid token available
        """
        await self.ensure_authenticated()
        token = self.token_storage.get_access_token()
        if not token:
            raise OAuth2Error("No access token available after authentication")
        return token

    async def get_user_info(self) -> dict:
        """Get information about the authenticated user.

        Returns:
            User info from OAuth2 resource endpoint

        Raises:
            OAuth2Error: If request fails
        """
        client = await self._get_http_client()

        data = {
            "client_id": self.settings.worksection_client_id,
            "client_secret": self.settings.worksection_client_secret,
            "access_token": await self.get_valid_token(),
        }

        url = f"{self.settings.oauth2_base_url}/oauth2/resource"
        response = await client.post(url, data=data)

        if response.status_code != 200:
            raise OAuth2Error(f"Failed to get user info: {response.text}")

        return response.json()

    def has_tokens(self) -> bool:
        """Check if we have stored tokens (may be expired).

        Returns:
            True if tokens exist
        """
        return self.token_storage.load() is not None

    def clear_tokens(self) -> None:
        """Clear all stored tokens (logout)."""
        self.token_storage.delete()
        logger.info("Tokens cleared")
