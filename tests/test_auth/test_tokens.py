"""Tests for token storage."""

import pytest

from worksection_mcp.auth.tokens import TokenStorage


class TestTokenStorage:
    """Test token storage functionality."""

    @pytest.fixture
    def token_storage(self, temp_data_dir):
        """Create token storage instance."""
        return TokenStorage(storage_path=temp_data_dir / "tokens")

    @pytest.fixture
    def sample_token_response(self):
        """Sample OAuth2 token response."""
        return {
            "access_token": "test_access_token_12345",
            "refresh_token": "test_refresh_token_67890",
            "token_type": "Bearer",
            "expires_in": 86400,
            "account_url": "https://test.worksection.com",
        }

    def test_save_and_load_tokens(self, token_storage, sample_token_response):
        """Test saving and loading tokens."""
        # Save tokens
        token_storage.save(sample_token_response)

        # Load tokens
        loaded = token_storage.load()

        assert loaded is not None
        assert loaded["access_token"] == sample_token_response["access_token"]
        assert loaded["refresh_token"] == sample_token_response["refresh_token"]
        assert loaded["token_type"] == sample_token_response["token_type"]
        assert loaded["account_url"] == sample_token_response["account_url"]

    def test_token_not_found(self, token_storage):
        """Test loading when no tokens exist."""
        loaded = token_storage.load()
        assert loaded is None

    def test_delete_tokens(self, token_storage, sample_token_response):
        """Test deleting tokens."""
        token_storage.save(sample_token_response)
        assert token_storage.load() is not None

        token_storage.delete()
        assert token_storage.load() is None

    def test_is_access_token_valid_fresh_token(self, token_storage, sample_token_response):
        """Test that fresh tokens are valid."""
        token_storage.save(sample_token_response)

        assert token_storage.is_access_token_valid() is True

    def test_is_access_token_valid_expired_token(self, token_storage):
        """Test that expired tokens are invalid."""
        # Create token that expires in 1 minute (within 5 min buffer)
        expired_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 60,  # 1 minute
            "account_url": "https://test.worksection.com",
        }
        token_storage.save(expired_response)

        # Token should be considered invalid (within 5 min buffer)
        assert token_storage.is_access_token_valid() is False

    def test_get_access_token(self, token_storage, sample_token_response):
        """Test getting access token."""
        token_storage.save(sample_token_response)

        token = token_storage.get_access_token()
        assert token == sample_token_response["access_token"]

    def test_get_refresh_token(self, token_storage, sample_token_response):
        """Test getting refresh token."""
        token_storage.save(sample_token_response)

        token = token_storage.get_refresh_token()
        assert token == sample_token_response["refresh_token"]

    def test_encryption_key_generation(self, temp_data_dir):
        """Test that encryption key is auto-generated."""
        storage1 = TokenStorage(storage_path=temp_data_dir / "tokens1")
        storage2 = TokenStorage(storage_path=temp_data_dir / "tokens1")  # Same path

        # Both should use the same key
        assert storage1._key == storage2._key

    def test_different_storage_different_keys(self, temp_data_dir):
        """Test that different storages have different keys."""
        storage1 = TokenStorage(storage_path=temp_data_dir / "tokens1")
        storage2 = TokenStorage(storage_path=temp_data_dir / "tokens2")

        # Different paths should have different keys
        assert storage1._key != storage2._key
