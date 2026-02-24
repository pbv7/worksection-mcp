"""Tests for response truncation utility."""

from datetime import UTC, datetime

from worksection_mcp.utils.response_utils import truncate_response, truncate_to_size


def test_no_truncation_needed():
    """Should return all items when under limit."""
    data = [1, 2, 3]
    result = truncate_response(data, max_results=10)
    assert result["items"] == [1, 2, 3]
    assert result["total_count"] == 3
    assert result["returned_count"] == 3
    assert result["truncated"] is False
    assert result["offset"] == 0


def test_truncation():
    """Should truncate when over limit."""
    data = list(range(200))
    result = truncate_response(data, max_results=50)
    assert result["total_count"] == 200
    assert result["returned_count"] == 50
    assert result["truncated"] is True
    assert result["items"] == list(range(50))


def test_offset():
    """Should skip items when offset provided."""
    data = list(range(100))
    result = truncate_response(data, max_results=10, offset=90)
    assert result["items"] == list(range(90, 100))
    assert result["total_count"] == 100
    assert result["returned_count"] == 10
    assert result["truncated"] is False


def test_offset_with_truncation():
    """Should handle offset + truncation together."""
    data = list(range(100))
    result = truncate_response(data, max_results=10, offset=50)
    assert result["items"] == list(range(50, 60))
    assert result["truncated"] is True


def test_empty_list():
    """Should handle empty list."""
    result = truncate_response([], max_results=100)
    assert result["items"] == []
    assert result["total_count"] == 0
    assert result["truncated"] is False


def test_exact_limit():
    """Should not truncate when exactly at limit."""
    data = list(range(10))
    result = truncate_response(data, max_results=10)
    assert result["truncated"] is False
    assert result["returned_count"] == 10


# --- truncate_to_size tests ---


def test_truncate_to_size_under_cap():
    """Under size cap should return unmodified with was_truncated=False."""
    data = [{"id": i} for i in range(5)]
    result, was_truncated = truncate_to_size(data, max_bytes=100_000)
    assert result == data
    assert was_truncated is False


def test_truncate_to_size_over_cap():
    """Over size cap should truncate with was_truncated=True."""
    data = [{"id": i, "payload": "x" * 1000} for i in range(100)]
    result, was_truncated = truncate_to_size(data, max_bytes=5000)
    assert was_truncated is True
    assert len(result) < len(data)
    assert len(result) > 0


def test_truncate_to_size_empty_list():
    """Empty list should return empty with was_truncated=False."""
    result, was_truncated = truncate_to_size([])
    assert result == []
    assert was_truncated is False


def test_truncate_to_size_non_serializable():
    """Non-serializable values like datetime should be handled via default=str."""
    data = [
        {"ts": datetime(2024, 1, 1, 12, 0, tzinfo=UTC)},
        {"ts": datetime(2024, 6, 15, 8, 30, tzinfo=UTC)},
    ]
    result, was_truncated = truncate_to_size(data, max_bytes=100_000)
    assert result == data
    assert was_truncated is False
