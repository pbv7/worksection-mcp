"""Protocol types for MCP registration functions.

These protocols describe the minimal decorator interface used by this project.
They allow registration code to accept both FastMCP instances and lightweight
test doubles without losing static type safety.
"""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class ToolRegistrar(Protocol):
    """Minimal protocol for objects that can register MCP tools."""

    def tool(self) -> Callable[[Callable[..., Awaitable[Any]]], Any]:
        """Return a decorator that registers an async tool function."""
        ...


class ResourceRegistrar(Protocol):
    """Minimal protocol for objects that can register MCP resources."""

    def resource(self, uri: str) -> Callable[[Callable[..., Awaitable[Any]]], Any]:
        """Return a decorator that registers an async resource function."""
        ...
