"""Tests for token storage resilience and key management lifecycle."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from worksection_mcp.auth.tokens import TokenStorage


class TestKeyManagementLifecycle:
    """Verify encryption key selection, validation, and fallback behavior.

    TokenStorage accepts an optional encryption key.  When the key is valid
    Fernet material it must be used directly.  When it is garbage the storage
    must recover gracefully (generate a new key) so the server never fails to
    start because of a mis-configured environment variable.
    """

    def test_valid_fernet_key_is_accepted(self, temp_data_dir):
        """A well-formed Fernet key passed via config should be used verbatim."""
        key = Fernet.generate_key()
        storage = TokenStorage(
            storage_path=temp_data_dir / "tokens-valid",
            encryption_key=key.decode(),
        )
        assert storage._key == key

    def test_invalid_key_triggers_fallback_generation(self, temp_data_dir):
        """An un-parseable key should cause automatic generation, not a crash."""
        storage = TokenStorage(
            storage_path=temp_data_dir / "tokens-bad",
            encryption_key="definitely-not-base64-fernet",
        )
        # Should still produce a usable Fernet key
        Fernet(storage._key)  # will raise if invalid


class TestTokenLoadResilience:
    """Ensure load() never crashes on corrupted or tampered storage files.

    In production tokens can be corrupted by partial writes, key rotation,
    or manual editing.  load() must return None with a log message rather
    than propagating exceptions.
    """

    @pytest.fixture
    def storage(self, temp_data_dir):
        return TokenStorage(storage_path=temp_data_dir / "tokens")

    def test_corrupted_ciphertext_returns_none(self, storage):
        """Random bytes where an encrypted file is expected should yield None."""
        storage._token_file.write_bytes(b"random-garbage-not-fernet-at-all")
        assert storage.load() is None

    def test_valid_encryption_invalid_json_returns_none(self, storage):
        """A correctly encrypted payload with non-JSON content should yield None."""
        encrypted = storage._fernet.encrypt(b"<this is not json>")
        storage._token_file.write_bytes(encrypted)
        assert storage.load() is None


class TestTokenValidityEdgeCases:
    """Test token validity evaluation for boundary conditions."""

    @pytest.fixture
    def storage(self, temp_data_dir):
        return TokenStorage(storage_path=temp_data_dir / "tokens")

    @pytest.fixture
    def _save_short_lived_token(self, storage):
        """Save a token that expires within the 5-minute validity buffer."""
        storage.save(
            {
                "access_token": "short-lived",
                "refresh_token": "refresh",
                "token_type": "Bearer",
                "expires_in": 60,  # 1 minute — well inside the 5-min buffer
                "account_url": "https://test.worksection.com",
            }
        )

    def test_no_stored_tokens_means_invalid(self, storage):
        """When no tokens exist on disk, is_access_token_valid should be False."""
        assert storage.is_access_token_valid() is False

    @pytest.mark.usefixtures("_save_short_lived_token")
    def test_near_expiry_token_considered_invalid(self, storage):
        """A token expiring within the 5-minute buffer should be treated as invalid."""
        assert storage.is_access_token_valid() is False

    @pytest.mark.usefixtures("_save_short_lived_token")
    def test_get_access_token_returns_none_for_expired(self, storage):
        """get_access_token must return None rather than an expired token string."""
        assert storage.get_access_token() is None
