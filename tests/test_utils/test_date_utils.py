"""Tests for date utilities."""

import pytest

from worksection_mcp.utils.date_utils import (
    format_date_for_api,
    validate_date_range,
    validate_period,
)


class TestFormatDateForApi:
    """Tests for format_date_for_api function."""

    def test_converts_iso_format_to_api_format(self):
        """YYYY-MM-DD should be converted to DD.MM.YYYY."""
        assert format_date_for_api("2024-01-15") == "15.01.2024"

    def test_passes_through_api_format(self):
        """DD.MM.YYYY should be returned as-is."""
        assert format_date_for_api("15.01.2024") == "15.01.2024"

    def test_returns_none_for_none_input(self):
        """None input should return None."""
        assert format_date_for_api(None) is None

    def test_returns_none_for_empty_string(self):
        """Empty string should return None."""
        assert format_date_for_api("") is None

    def test_converts_various_dates(self):
        """Test conversion of various dates."""
        assert format_date_for_api("2023-12-31") == "31.12.2023"
        assert format_date_for_api("2024-02-29") == "29.02.2024"
        assert format_date_for_api("2025-06-01") == "01.06.2025"

    def test_passes_through_non_iso_strings(self):
        """Non-ISO format strings should pass through unchanged."""
        assert format_date_for_api("01.01.2024") == "01.01.2024"
        assert format_date_for_api("2024/01/15") == "2024/01/15"


class TestValidatePeriod:
    """Tests for validate_period function."""

    def test_valid_minute_periods(self):
        """Valid minute periods should return True."""
        assert validate_period("1m") is True
        assert validate_period("60m") is True
        assert validate_period("120m") is True
        assert validate_period("360m") is True

    def test_invalid_minute_periods(self):
        """Invalid minute periods should return False."""
        assert validate_period("0m") is False
        assert validate_period("361m") is False
        assert validate_period("400m") is False

    def test_valid_hour_periods(self):
        """Valid hour periods should return True."""
        assert validate_period("1h") is True
        assert validate_period("24h") is True
        assert validate_period("48h") is True
        assert validate_period("72h") is True

    def test_invalid_hour_periods(self):
        """Invalid hour periods should return False."""
        assert validate_period("0h") is False
        assert validate_period("73h") is False
        assert validate_period("100h") is False

    def test_valid_day_periods(self):
        """Valid day periods should return True."""
        assert validate_period("1d") is True
        assert validate_period("7d") is True
        assert validate_period("14d") is True
        assert validate_period("30d") is True

    def test_invalid_day_periods(self):
        """Invalid day periods should return False."""
        assert validate_period("0d") is False
        assert validate_period("31d") is False
        assert validate_period("100d") is False

    def test_invalid_formats(self):
        """Invalid formats should return False."""
        assert validate_period("") is False
        assert validate_period("3") is False
        assert validate_period("d") is False
        assert validate_period("3x") is False
        assert validate_period("invalid") is False
        assert validate_period("3 days") is False
        assert validate_period("-1d") is False


class TestValidateDateRange:
    """Tests for validate_date_range function."""

    def test_valid_iso_dates(self):
        """Valid ISO date range should not raise."""
        validate_date_range("2024-01-01", "2024-12-31")

    def test_valid_api_dates(self):
        """Valid DD.MM.YYYY date range should not raise."""
        validate_date_range("01.01.2024", "31.12.2024")

    def test_none_dates_ok(self):
        """None dates should not raise."""
        validate_date_range(None, None)
        validate_date_range("2024-01-01", None)
        validate_date_range(None, "2024-12-31")

    def test_same_date_ok(self):
        """Same start and end date should not raise."""
        validate_date_range("2024-06-15", "2024-06-15")

    def test_start_after_end_raises(self):
        """Start date after end date should raise ValueError."""
        with pytest.raises(ValueError, match="must not be after"):
            validate_date_range("2024-12-31", "2024-01-01")

    def test_invalid_format_raises(self):
        """Invalid date format should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_range("2024/01/15", "2024-12-31")

    def test_impossible_date_raises(self):
        """Impossible date (e.g., Feb 30) should raise ValueError."""
        with pytest.raises(ValueError, match=r"must be in range|day is out of range"):
            validate_date_range("2024-02-30", "2024-12-31")

    def test_mixed_formats_ok(self):
        """Mixed ISO and DD.MM.YYYY should work."""
        validate_date_range("2024-01-01", "31.12.2024")
