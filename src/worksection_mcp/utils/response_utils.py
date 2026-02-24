"""Response utilities for MCP tools."""

import json
from typing import Any

MAX_RESPONSE_BYTES = 850_000


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


def truncate_to_size(
    data: list[Any],
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> tuple[list[Any], bool]:
    """Truncate a list so its JSON serialization stays under max_bytes.

    Uses binary search to find the maximum number of items that fit.

    Args:
        data: List of items to potentially truncate
        max_bytes: Maximum JSON size in bytes

    Returns:
        Tuple of (truncated_list, was_truncated)
    """
    if not data:
        return data, False

    serialized = json.dumps(data, default=str)
    if len(serialized.encode("utf-8")) <= max_bytes:
        return data, False

    # Binary search for max items that fit
    lo, hi = 0, len(data)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        size = len(json.dumps(data[:mid], default=str).encode("utf-8"))
        if size <= max_bytes:
            lo = mid
        else:
            hi = mid - 1

    return data[:lo], True
