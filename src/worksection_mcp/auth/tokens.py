"""Token storage with encryption."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class TokenData(TypedDict):
    """Structure for stored token data."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    account_url: str
    created_at: str
    expires_at: str


class TokenStorage:
    """Secure token storage with Fernet encryption."""

    TOKEN_FILE = "tokens.enc"

    def __init__(self, storage_path: Path, encryption_key: str = ""):
        """Initialize token storage.

        Args:
            storage_path: Directory for storing tokens
            encryption_key: Fernet encryption key (auto-generated if empty)
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._key = self._get_or_create_key(encryption_key)
        self._fernet = Fernet(self._key)
        self._token_file = self.storage_path / self.TOKEN_FILE

    def _get_or_create_key(self, provided_key: str) -> bytes:
        """Get or create encryption key."""
        key_file = self.storage_path / "key.key"

        if provided_key:
            # Use provided key (must be valid Fernet key)
            key = provided_key.encode() if isinstance(provided_key, str) else provided_key
            # Validate it's a valid Fernet key
            try:
                Fernet(key)
                return key
            except Exception:
                logger.warning("Invalid encryption key provided, generating new one")

        # Check for existing key file
        if key_file.exists():
            return key_file.read_bytes()

        # Generate new key
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        logger.info(f"Generated new encryption key at {key_file}")
        return key

    def save(self, token_response: dict) -> None:
        """Save token response with encryption.

        Args:
            token_response: Token response from OAuth2 token endpoint
        """
        now = datetime.now(timezone.utc)
        expires_in = token_response.get("expires_in", 86400)

        token_data: TokenData = {
            "access_token": token_response["access_token"],
            "refresh_token": token_response["refresh_token"],
            "token_type": token_response.get("token_type", "Bearer"),
            "expires_in": expires_in,
            "account_url": token_response.get("account_url", ""),
            "created_at": now.isoformat(),
            "expires_at": datetime.fromtimestamp(
                now.timestamp() + expires_in, tz=timezone.utc
            ).isoformat(),
        }

        encrypted = self._fernet.encrypt(json.dumps(token_data).encode())
        self._token_file.write_bytes(encrypted)
        logger.info("Tokens saved successfully")

    def load(self) -> TokenData | None:
        """Load and decrypt stored tokens.

        Returns:
            Token data or None if not found
        """
        if not self._token_file.exists():
            logger.debug("No stored tokens found")
            return None

        try:
            encrypted = self._token_file.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            token_data: TokenData = json.loads(decrypted)
            logger.debug("Tokens loaded successfully")
            return token_data
        except InvalidToken:
            logger.error("Failed to decrypt tokens - key may have changed")
            return None
        except json.JSONDecodeError:
            logger.error("Failed to parse token data")
            return None

    def delete(self) -> None:
        """Delete stored tokens."""
        if self._token_file.exists():
            self._token_file.unlink()
            logger.info("Tokens deleted")

    def is_access_token_valid(self, token_data: TokenData | None = None) -> bool:
        """Check if access token is still valid.

        Args:
            token_data: Token data to check (loads from storage if None)

        Returns:
            True if access token is valid
        """
        if token_data is None:
            token_data = self.load()

        if not token_data:
            return False

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        now = datetime.now(timezone.utc)

        # Consider token invalid 5 minutes before expiry
        buffer_seconds = 300
        is_valid = (expires_at.timestamp() - now.timestamp()) > buffer_seconds

        if not is_valid:
            logger.debug("Access token expired or expiring soon")

        return is_valid

    def get_access_token(self) -> str | None:
        """Get the current access token if valid.

        Returns:
            Access token or None
        """
        token_data = self.load()
        if token_data and self.is_access_token_valid(token_data):
            return token_data["access_token"]
        return None

    def get_refresh_token(self) -> str | None:
        """Get the refresh token.

        Returns:
            Refresh token or None
        """
        token_data = self.load()
        return token_data["refresh_token"] if token_data else None
