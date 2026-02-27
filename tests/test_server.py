"""Tests for server wiring, lifecycle, and entrypoints."""

from __future__ import annotations

import importlib
import runpy
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.helpers import build_settings
from worksection_mcp import get_mcp as package_get_mcp
from worksection_mcp import main as package_main
from worksection_mcp import server as server_module
from worksection_mcp.logging_config import build_logging_dict


class FakeFastMCP:
    """Small FastMCP test double to observe lifecycle/run wiring."""

    def __init__(self, name: str, instructions: str, lifespan):
        self.name = name
        self.instructions = instructions
        self.lifespan = lifespan
        self.run = MagicMock()


@pytest.mark.asyncio
async def test_create_server_wires_dependencies_and_lifecycle(monkeypatch, tmp_path):
    """create_server should initialize dependencies and clean up on shutdown."""
    settings = build_settings(tmp_path)

    def _noop_ensure_directories(_self):
        return None

    def _fake_validate_resources(_self):
        return {
            "dns_resolution": "✓ ok",
            "token_storage_writable": "✓ ok",
            "file_cache_writable": "✓ ok",
            "ssl_cert_dir": "✓ ok",
        }

    monkeypatch.setattr(
        server_module.Settings,
        "ensure_directories",
        _noop_ensure_directories,
    )
    monkeypatch.setattr(
        server_module.Settings,
        "validate_external_resources",
        _fake_validate_resources,
    )

    oauth = SimpleNamespace(ensure_authenticated=AsyncMock(), close=AsyncMock())
    client = SimpleNamespace(
        me=AsyncMock(return_value={"id": "u1"}), close=AsyncMock(), settings=settings
    )
    file_cache = SimpleNamespace(close=AsyncMock())
    register_tools = MagicMock()
    register_resources = MagicMock()

    monkeypatch.setattr(server_module, "FastMCP", FakeFastMCP)
    monkeypatch.setattr(server_module, "OAuth2Manager", lambda _settings: oauth)
    monkeypatch.setattr(server_module, "WorksectionClient", lambda _oauth, _settings: client)
    monkeypatch.setattr(server_module, "FileCache", lambda **_kwargs: file_cache)
    monkeypatch.setattr(server_module, "register_all_tools", register_tools)
    monkeypatch.setattr(server_module, "register_file_resources", register_resources)

    server, _log_config = server_module.create_server(settings)
    mcp = cast(FakeFastMCP, server)
    assert isinstance(mcp, FakeFastMCP)
    assert mcp.name == settings.mcp_server_name
    assert mcp.instructions is not None
    assert "Worksection MCP Server" in mcp.instructions
    register_tools.assert_called_once()
    register_resources.assert_called_once()

    async with mcp.lifespan(mcp):
        oauth.ensure_authenticated.assert_awaited_once()
        client.me.assert_awaited_once()

    client.close.assert_awaited_once()
    file_cache.close.assert_awaited_once()


def test_get_mcp_is_lazy_and_cached(monkeypatch):
    """get_mcp should create once and return cached instance afterwards."""
    created = []

    def fake_create_server():
        created.append("created")
        return {"name": "server"}, {}

    monkeypatch.setattr(server_module, "create_server", fake_create_server)
    server_module._mcp = None

    first = server_module.get_mcp()
    second = server_module.get_mcp()

    assert first == second == {"name": "server"}  # type: ignore[comparison-overlap]
    assert len(created) == 1


def test_server_main_selects_transport(monkeypatch, tmp_path):
    """main should call FastMCP.run with the configured transport."""
    settings = build_settings(tmp_path, mcp_transport="stdio")
    stdio_server = SimpleNamespace(run=MagicMock())
    monkeypatch.setattr(server_module, "get_settings", lambda: settings)
    monkeypatch.setattr(server_module, "create_server", lambda _settings: (stdio_server, {}))
    server_module.main()
    stdio_server.run.assert_called_once_with(transport="stdio")

    streamable_http_settings = build_settings(
        tmp_path,
        mcp_transport="streamable-http",
        mcp_server_host="127.0.0.1",
        mcp_server_port=9000,
    )
    log_config = build_logging_dict(streamable_http_settings)
    streamable_http_server = SimpleNamespace(run=MagicMock())
    monkeypatch.setattr(server_module, "get_settings", lambda: streamable_http_settings)
    monkeypatch.setattr(
        server_module,
        "create_server",
        lambda _settings: (streamable_http_server, log_config),
    )
    server_module.main()
    streamable_http_server.run.assert_called_once()
    call_kwargs = streamable_http_server.run.call_args.kwargs
    assert call_kwargs["transport"] == "streamable-http"
    assert call_kwargs["host"] == "127.0.0.1"
    assert call_kwargs["port"] == 9000
    assert call_kwargs["uvicorn_config"]["timeout_graceful_shutdown"] == 5
    assert call_kwargs["uvicorn_config"]["access_log"] is True
    assert call_kwargs["uvicorn_config"]["log_config"] is log_config


def test_request_log_mode_off_disables_access_log(monkeypatch, tmp_path):
    """REQUEST_LOG_MODE=OFF should disable Uvicorn access logging."""
    off_settings = build_settings(
        tmp_path,
        mcp_transport="streamable-http",
        mcp_server_host="127.0.0.1",
        mcp_server_port=9001,
        request_log_mode="OFF",
    )
    off_log_config = build_logging_dict(off_settings)
    off_server = SimpleNamespace(run=MagicMock())
    monkeypatch.setattr(server_module, "get_settings", lambda: off_settings)
    monkeypatch.setattr(
        server_module,
        "create_server",
        lambda _settings: (off_server, off_log_config),
    )
    server_module.main()
    off_call_kwargs = off_server.run.call_args.kwargs
    assert off_call_kwargs["uvicorn_config"]["access_log"] is False


def test_invalid_transport_rejected(tmp_path):
    """Pydantic should reject unsupported transport values."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        build_settings(tmp_path, mcp_transport="sse")


def test_package_entrypoints_delegate_to_server(monkeypatch):
    """Package-level main/get_mcp helpers should proxy server module entrypoints."""
    monkeypatch.setattr("worksection_mcp.server.main", lambda: "ok-main")
    monkeypatch.setattr("worksection_mcp.server.mcp", "mcp-instance")
    assert package_main() == "ok-main"
    assert package_get_mcp() == "mcp-instance"


def test_python_module_entrypoint_executes_server_main(monkeypatch):
    """Running worksection_mcp.__main__ should invoke server.main."""
    calls = []
    monkeypatch.setattr("worksection_mcp.server.main", lambda: calls.append("called"))
    runpy.run_module("worksection_mcp.__main__", run_name="__main__")
    assert calls == ["called"]


def test_resources_and_package_exports():
    """Public exports should expose expected symbols."""
    resources_module = importlib.import_module("worksection_mcp.resources")
    assert "register_file_resources" in resources_module.__all__

    package_module = importlib.import_module("worksection_mcp")
    assert package_module.__all__ == ["__version__", "get_mcp", "main"]


def test_format_authenticated_user_logs_only_id_and_name():
    """Auth user log summary should avoid sensitive fields like email."""
    user_payload = {
        "status": "ok",
        "data": {
            "id": "555235",
            "name": "Bohdan Potishuk",
            "email": "bogdan@atollholding.com.ua",
            "avatar": "https://example.com/avatar.jpg",
        },
    }

    summary = server_module._format_authenticated_user(user_payload)
    assert "id=555235" in summary
    assert "name=Bohdan Potishuk" in summary
    assert "email" not in summary
    assert "avatar" not in summary
