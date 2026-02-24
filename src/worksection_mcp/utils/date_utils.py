"""Date and period utilities for Worksection API."""

import re
from datetime import date


def format_date_for_api(date_str: str | None) -> str | None:
    """Convert date to DD.MM.YYYY format for Worksection API calls.

    The Worksection API expects dates in DD.MM.YYYY format for cost/time
    tracking endpoints (get_costs, get_costs_total).

    Accepts both formats:
    - YYYY-MM-DD (ISO format) -> converts to DD.MM.YYYY
    - DD.MM.YYYY (API format) -> returns as-is

    Args:
        date_str: Date string in either format, or None

    Returns:
        Date in DD.MM.YYYY format, or None if input was None

    Examples:
        >>> format_date_for_api("2024-01-15")
        '15.01.2024'
        >>> format_date_for_api("15.01.2024")
        '15.01.2024'
        >>> format_date_for_api(None)
        None
    """
    if not date_str:
        return None

    # Check if it's ISO format (YYYY-MM-DD)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        parts = date_str.split("-")
        return f"{parts[2]}.{parts[1]}.{parts[0]}"

    # Assume it's already in DD.MM.YYYY format or pass through as-is
    return date_str


def validate_period(period: str) -> bool:
    """Validate period format for get_events API endpoint.

    The Worksection API get_events endpoint accepts a period parameter
    with the following formats:
    - Minutes: 1m to 360m (1 minute to 6 hours)
    - Hours: 1h to 72h (1 hour to 3 days)
    - Days: 1d to 30d (1 day to 30 days)

    Args:
        period: Period string like "3d", "24h", "120m"

    Returns:
        True if period format is valid, False otherwise

    Examples:
        >>> validate_period("3d")
        True
        >>> validate_period("24h")
        True
        >>> validate_period("120m")
        True
        >>> validate_period("400m")
        False
        >>> validate_period("100d")
        False
        >>> validate_period("invalid")
        False
    """
    match = re.match(r"^(\d+)([mhd])$", period)
    if not match:
        return False

    value = int(match.group(1))
    unit = match.group(2)

    max_values = {"m": 360, "h": 72, "d": 30}
    max_val = max_values.get(unit)
    return max_val is not None and 1 <= value <= max_val


def _parse_date(date_str: str) -> date:
    """Parse a date string in ISO or DD.MM.YYYY format.

    Args:
        date_str: Date string

    Returns:
        Parsed date

    Raises:
        ValueError: If the date format is invalid or the date is not real
    """
    # Try ISO format first (YYYY-MM-DD)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        year, month, day = (int(p) for p in date_str.split("-"))
        return date(year, month, day)

    # Try DD.MM.YYYY format
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str):
        parts = date_str.split(".")
        return date(int(parts[2]), int(parts[1]), int(parts[0]))

    raise ValueError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD or DD.MM.YYYY.")


def validate_date_range(
    date_start: str | None = None,
    date_end: str | None = None,
) -> None:
    """Validate a date range: format, reality, and start <= end.

    Args:
        date_start: Start date (optional)
        date_end: End date (optional)

    Raises:
        ValueError: If dates are invalid or start > end
    """
    parsed_start = None
    parsed_end = None

    if date_start:
        parsed_start = _parse_date(date_start)

    if date_end:
        parsed_end = _parse_date(date_end)

    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise ValueError(f"date_start ({date_start}) must not be after date_end ({date_end})")
