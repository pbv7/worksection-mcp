"""Shared test helpers for MCP tool and settings tests."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from worksection_mcp.config import Settings


class FakeMCP:
    """Minimal MCP-like object for unit testing tool/resource registration."""

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Awaitable[Any]]] = {}
        self.resources: dict[str, Callable[..., Awaitable[Any]]] = {}
        self.resource_patterns: dict[str, str] = {}

    def tool(self) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        """Decorator that registers a tool by function name."""

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self.tools[func.__name__] = func
            return func

        return decorator

    def resource(
        self,
        pattern: str,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        """Decorator that registers a resource by function name and URI pattern."""

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self.resources[func.__name__] = func
            self.resource_patterns[func.__name__] = pattern
            return func

        return decorator


def build_settings(temp_dir: Path, **overrides: Any) -> Settings:
    """Create a stable Settings object for tests."""
    base = {
        "worksection_client_id": "test_client_id_12345",
        "worksection_client_secret": "test_client_secret_value_123456",
        "worksection_account_url": "https://test.worksection.com",
        "worksection_redirect_uri": "https://localhost:8080/oauth/callback",
        "worksection_scopes": "projects_read,tasks_read,comments_read,users_read,files_read,tags_read,costs_read",
        "oauth_callback_use_ssl": True,
        "token_storage_path": temp_dir / "tokens",
        "file_cache_path": temp_dir / "files",
        "oauth_ssl_cert_path": temp_dir / "certs" / "callback.crt",
        "oauth_ssl_key_path": temp_dir / "certs" / "callback.key",
        "token_encryption_key": "",
        "mcp_server_host": "127.0.0.1",
    }
    base.update(overrides)
    return Settings(**base, _env_file=None)
