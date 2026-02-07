"""Tests for response truncation utility."""

from worksection_mcp.utils.response_utils import truncate_response


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
