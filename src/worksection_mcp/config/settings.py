"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OAuth2 Configuration (Required)
    worksection_client_id: str = Field(
        ...,
        description="OAuth2 client ID from Worksection app settings",
    )
    worksection_client_secret: str = Field(
        ...,
        description="OAuth2 client secret from Worksection app settings",
    )
    worksection_account_url: str = Field(
        ...,
        description="Worksection account URL (e.g., https://company.worksection.com)",
    )
    worksection_redirect_uri: str = Field(
        default="https://localhost:8080/oauth/callback",
        description="OAuth2 redirect URI",
    )
    worksection_scopes: str = Field(
        default="projects_read,tasks_read,timers_read,costs_read,comments_read,users_read",
        description="Comma-separated OAuth2 scopes",
    )

    # OAuth2 Flow Settings
    oauth_callback_host: str = Field(
        default="localhost",
        description="Host for OAuth callback server",
    )
    oauth_callback_port: int = Field(
        default=8080,
        description="Port for OAuth callback server",
    )
    oauth_auto_open_browser: bool = Field(
        default=True,
        description="Automatically open browser for OAuth authorization",
    )

    # SSL Configuration for OAuth Callback
    oauth_callback_use_ssl: bool = Field(
        default=True,
        description="Use HTTPS for OAuth callback server",
    )
    oauth_ssl_cert_path: Path = Field(
        default=Path("./data/certs/callback.crt"),
        description="Path to SSL certificate file",
    )
    oauth_ssl_key_path: Path = Field(
        default=Path("./data/certs/callback.key"),
        description="Path to SSL private key file",
    )
    oauth_ssl_cert_days: int = Field(
        default=365,
        description="Certificate validity in days for auto-generated certs",
    )

    # Token Management
    token_storage_path: Path = Field(
        default=Path("./data/tokens"),
        description="Directory for storing encrypted tokens",
    )
    token_encryption_key: str = Field(
        default="",
        description="Encryption key for tokens (auto-generated if empty)",
    )

    # File Caching
    file_cache_path: Path = Field(
        default=Path("./data/files"),
        description="Directory for cached file attachments",
    )
    file_cache_retention_hours: int = Field(
        default=24,
        description="How long to keep cached files (hours)",
    )
    max_file_size_mb: int = Field(
        default=10,
        description="Maximum file size to cache (MB)",
    )

    # MCP Server Configuration
    mcp_server_name: str = Field(
        default="worksection",
        description="Server name used in MCP protocol",
    )
    mcp_server_port: int = Field(
        default=8000,
        description="Server port for SSE transport",
    )
    mcp_transport: Literal["sse", "stdio"] = Field(
        default="sse",
        description="MCP transport type",
    )

    # Runtime Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment",
    )

    @field_validator("worksection_account_url")
    @classmethod
    def validate_account_url(cls, v: str) -> str:
        """Ensure account URL doesn't have trailing slash."""
        return v.rstrip("/")

    @field_validator(
        "token_storage_path", "file_cache_path", "oauth_ssl_cert_path", "oauth_ssl_key_path",
        mode="before",
    )
    @classmethod
    def ensure_path(cls, v):
        """Convert string to Path."""
        path = Path(v) if isinstance(v, str) else v
        return path

    @property
    def scopes_list(self) -> list[str]:
        """Return scopes as a list."""
        return [s.strip() for s in self.worksection_scopes.split(",")]

    @property
    def oauth2_base_url(self) -> str:
        """Return the OAuth2 base URL."""
        return "https://worksection.com"

    @property
    def api_base_url(self) -> str:
        """Return the API base URL for the account."""
        return f"{self.worksection_account_url}/api/oauth2"

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.token_storage_path.mkdir(parents=True, exist_ok=True)
        self.file_cache_path.mkdir(parents=True, exist_ok=True)
        # Create SSL certificates directory
        self.oauth_ssl_cert_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
