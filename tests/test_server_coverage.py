"""Tests for server lifecycle edge cases: validation failures and auth errors."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.helpers import build_settings
from worksection_mcp import server as server_module


class FakeFastMCP:
    """Test double that captures constructor args and lifecycle."""

    def __init__(self, name: str, instructions: str, lifespan: Any):
        self.name = name
        self.instructions = instructions
        self.lifespan = lifespan
        self.run = MagicMock()


def _patch_server_deps(monkeypatch, *, oauth=None, client=None, file_cache=None):
    """Patch all create_server dependencies with sensible defaults."""
    oauth = oauth or SimpleNamespace(
        ensure_authenticated=AsyncMock(),
        close=AsyncMock(),
    )
    client = client or SimpleNamespace(
        me=AsyncMock(return_value={"id": "u1"}),
        close=AsyncMock(),
    )
    file_cache = file_cache or SimpleNamespace(close=AsyncMock())

    monkeypatch.setattr(server_module, "FastMCP", FakeFastMCP)
    monkeypatch.setattr(server_module, "OAuth2Manager", lambda _s: oauth)
    monkeypatch.setattr(server_module, "WorksectionClient", lambda _o, _s: client)
    monkeypatch.setattr(server_module, "FileCache", lambda **_kw: file_cache)
    monkeypatch.setattr(server_module, "register_all_tools", MagicMock())
    monkeypatch.setattr(server_module, "register_file_resources", MagicMock())

    return oauth, client, file_cache


@pytest.mark.asyncio
async def test_validation_errors_logged_but_do_not_block_startup(monkeypatch, tmp_path):
    """When validate_external_resources reports failures, the server should
    still start (with a warning), not crash.  This covers the has_errors branch
    and the error-level logging for individual validation keys."""
    settings = build_settings(tmp_path)

    def _failing_validate(_self):
        return {
            "dns_resolution": "✗ Cannot resolve test.worksection.com",
            "token_storage_writable": "✓ ok",
            "file_cache_writable": "✗ Cannot write to /readonly",
            "ssl_cert_dir": "✓ ok",
        }

    monkeypatch.setattr(server_module.Settings, "ensure_directories", lambda _self: None)
    monkeypatch.setattr(server_module.Settings, "validate_external_resources", _failing_validate)
    _patch_server_deps(monkeypatch)

    # create_server should succeed despite validation failures
    mcp = server_module.create_server(settings)
    assert isinstance(mcp, FakeFastMCP)


@pytest.mark.asyncio
async def test_lifespan_propagates_auth_failure(monkeypatch, tmp_path):
    """If OAuth authentication fails during lifespan startup, the error must
    propagate so the server does not silently run without credentials."""
    settings = build_settings(tmp_path)

    monkeypatch.setattr(server_module.Settings, "ensure_directories", lambda _self: None)
    monkeypatch.setattr(
        server_module.Settings,
        "validate_external_resources",
        lambda _self: {
            "dns_resolution": "✓ ok",
            "token_storage_writable": "✓ ok",
            "file_cache_writable": "✓ ok",
            "ssl_cert_dir": "✓ ok",
        },
    )

    failing_oauth = SimpleNamespace(
        ensure_authenticated=AsyncMock(side_effect=RuntimeError("OAuth flow failed")),
        close=AsyncMock(),
    )
    _patch_server_deps(monkeypatch, oauth=failing_oauth)

    mcp = server_module.create_server(settings)
    assert isinstance(mcp, FakeFastMCP)

    with pytest.raises(RuntimeError, match="OAuth flow failed"):
        async with mcp.lifespan(mcp):
            pass  # should not reach here
