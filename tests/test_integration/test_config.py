"""Tests for configuration."""

from typing import Any

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from worksection_mcp.config.settings import Settings


def _settings_kwargs(temp_data_dir, **overrides: Any) -> dict[str, Any]:
    """Build baseline settings kwargs for tests."""
    base: dict[str, Any] = {
        "worksection_client_id": "test_client_id",
        "worksection_client_secret": "test_client_secret_value_123456",
        "worksection_account_url": "https://test.worksection.com",
        "token_storage_path": temp_data_dir / "tokens",
        "file_cache_path": temp_data_dir / "files",
    }
    base.update(overrides)
    return base


class TestSettings:
    """Test configuration settings."""

    def test_required_fields(self, monkeypatch):
        """Test that required fields raise error if missing."""
        for env_name in (
            "WORKSECTION_CLIENT_ID",
            "WORKSECTION_CLIENT_SECRET",
            "WORKSECTION_ACCOUNT_URL",
        ):
            monkeypatch.delenv(env_name, raising=False)

        class SettingsWithoutEnv(Settings):
            model_config = SettingsConfigDict(
                env_file=None,
                case_sensitive=False,
                extra="ignore",
            )

        with pytest.raises(ValidationError, match="Field required"):
            # Should fail without required fields
            SettingsWithoutEnv.model_validate({})

    def test_with_required_fields(self, temp_data_dir):
        """Test settings with all required fields."""
        settings = Settings.model_validate(_settings_kwargs(temp_data_dir))

        assert settings.worksection_client_id == "test_client_id"
        assert settings.worksection_account_url == "https://test.worksection.com"

    def test_account_url_trailing_slash(self, temp_data_dir):
        """Test that trailing slash is removed from account URL."""
        settings = Settings.model_validate(
            _settings_kwargs(
                temp_data_dir,
                worksection_account_url="https://test.worksection.com/",
            )
        )

        assert not settings.worksection_account_url.endswith("/")

    def test_scopes_list(self, temp_data_dir):
        """Test scopes are parsed as list."""
        settings = Settings.model_validate(
            _settings_kwargs(
                temp_data_dir,
                worksection_scopes="projects_read,tasks_read,users_read",
            )
        )

        scopes = settings.scopes_list
        assert len(scopes) == 3
        assert "projects_read" in scopes
        assert "tasks_read" in scopes
        assert "users_read" in scopes

    def test_api_base_url(self, temp_data_dir):
        """Test API base URL property."""
        settings = Settings.model_validate(_settings_kwargs(temp_data_dir))

        assert settings.api_base_url == "https://test.worksection.com/api/oauth2"

    def test_ensure_directories(self, temp_data_dir):
        """Test directory creation."""
        token_path = temp_data_dir / "new_tokens"
        file_path = temp_data_dir / "new_files"

        settings = Settings.model_validate(
            _settings_kwargs(
                temp_data_dir,
                token_storage_path=token_path,
                file_cache_path=file_path,
            )
        )

        assert not token_path.exists()
        assert not file_path.exists()

        settings.ensure_directories()

        assert token_path.exists()
        assert file_path.exists()

    def test_max_file_size_bytes(self, temp_data_dir):
        """Test max file size conversion."""
        settings = Settings.model_validate(_settings_kwargs(temp_data_dir, max_file_size_mb=5))

        assert settings.max_file_size_bytes == 5 * 1024 * 1024

    def test_default_values(self, temp_data_dir):
        """Test default values are set."""
        settings = Settings.model_validate(_settings_kwargs(temp_data_dir))

        assert settings.mcp_server_port == 8000
        assert settings.mcp_transport == "sse"
        assert settings.log_level == "INFO"
        assert settings.environment == "development"
        assert settings.oauth_callback_port == 8080
