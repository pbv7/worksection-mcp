"""Response utilities for MCP tools."""

from typing import Any


def truncate_response(
    data: list[Any],
    max_results: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Apply client-side pagination to API response data.

    Args:
        data: List of items to paginate
        max_results: Maximum number of items to return
        offset: Number of items to skip from the start

    Returns:
        Dict with: items, total_count, returned_count, truncated, offset
    """
    total_count = len(data)
    sliced = data[offset : offset + max_results]
    return {
        "items": sliced,
        "total_count": total_count,
        "returned_count": len(sliced),
        "truncated": total_count > offset + max_results,
        "offset": offset,
    }
