"""Tests for OAuth callback handler and server."""

from __future__ import annotations

import asyncio
import ssl
from http.server import HTTPServer
from threading import Thread
from typing import cast

import httpx
import pytest

from worksection_mcp.auth.callback import CallbackHandler, CallbackServer


def _start_callback_handler_server(callback):
    """Start a plain HTTP server with CallbackHandler for request-level tests."""
    CallbackHandler.callback_received = staticmethod(callback)
    server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _stop_server(server: HTTPServer, thread: Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


def test_callback_handler_success_flow():
    """Handler should accept code/state and return success page."""
    received: list[tuple[str | None, str | None]] = []
    server, thread = _start_callback_handler_server(
        lambda code, state: received.append((code, state))
    )
    port = server.server_port
    try:
        response = httpx.get(f"http://127.0.0.1:{port}/oauth/callback?code=abc&state=s1")
        assert response.status_code == 200
        assert "Authorization Successful" in response.text
        assert received == [("abc", "s1")]
    finally:
        _stop_server(server, thread)


def test_callback_handler_error_flow():
    """Handler should render error page and callback with error details."""
    received: list[tuple[str | None, str | None]] = []
    server, thread = _start_callback_handler_server(
        lambda code, state: received.append((code, state))
    )
    port = server.server_port
    try:
        response = httpx.get(
            "http://127.0.0.1:"
            f"{port}/oauth/callback?error=access_denied&error_description=user+denied"
        )
        assert response.status_code == 200
        assert "Authorization Failed" in response.text
        assert received == [(None, "access_denied: user denied")]
    finally:
        _stop_server(server, thread)


def test_callback_handler_missing_code_and_wrong_path():
    """Handler should return 400 for missing code and 404 for unknown path."""
    server, thread = _start_callback_handler_server(lambda *_: None)
    port = server.server_port
    try:
        missing_code = httpx.get(f"http://127.0.0.1:{port}/oauth/callback")
        unknown_path = httpx.get(f"http://127.0.0.1:{port}/unknown")
        assert missing_code.status_code == 400
        assert unknown_path.status_code == 404
    finally:
        _stop_server(server, thread)


@pytest.mark.asyncio
async def test_callback_server_end_to_end_wait_for_callback():
    """CallbackServer should resolve wait_for_callback when handler receives code."""
    server = CallbackServer(host="127.0.0.1", port=0)
    server.start()
    try:
        assert server._server is not None
        actual_port = server._server.server_port

        wait_task = asyncio.create_task(server.wait_for_callback(timeout_seconds=1))
        await asyncio.sleep(0.05)
        async with httpx.AsyncClient() as async_client:
            response = await async_client.get(
                f"http://127.0.0.1:{actual_port}/oauth/callback?code=xyz&state=state-1"
            )
            assert response.status_code == 200

        code, state = await wait_task
        assert code == "xyz"
        assert state == "state-1"
    finally:
        server.stop()


@pytest.mark.asyncio
async def test_callback_server_timeout_and_url_property():
    """Server should timeout correctly and expose protocol-aware callback URL."""
    http_server = CallbackServer(host="localhost", port=8080, ssl_context=None)
    https_server = CallbackServer(
        host="localhost",
        port=8443,
        ssl_context=cast(ssl.SSLContext, object()),
    )

    assert http_server.callback_url == "http://localhost:8080/oauth/callback"
    assert https_server.callback_url == "https://localhost:8443/oauth/callback"

    with pytest.raises(asyncio.TimeoutError):
        await http_server.wait_for_callback(timeout_seconds=0.01)
