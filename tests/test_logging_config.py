"""Tests for centralized logging configuration."""

from __future__ import annotations

import logging

import pytest

from tests.helpers import build_settings
from worksection_mcp.logging_config import (
    ColorLevelFormatter,
    build_logging_dict,
    is_access_log_enabled,
)


def test_build_logging_dict_contains_expected_structure(tmp_path):
    """Logging config should define one formatter/handler pipeline for all key loggers."""
    settings = build_settings(tmp_path)
    log_config = build_logging_dict(settings, stderr_isatty=True)

    assert log_config["disable_existing_loggers"] is False
    assert log_config["formatters"]["standard"]["fmt"] == (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    assert log_config["formatters"]["standard"]["datefmt"] == "%Y-%m-%d %H:%M:%S"
    assert log_config["handlers"]["stderr"]["formatter"] == "standard"

    for logger_name in (
        "worksection_mcp",
        "fastmcp",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "httpx",
    ):
        assert logger_name in log_config["loggers"]
        assert log_config["loggers"][logger_name]["handlers"] == ["stderr"]
        assert log_config["loggers"][logger_name]["propagate"] is False


@pytest.mark.parametrize(
    ("request_log_mode", "expected_level", "expected_access_enabled"),
    [
        ("INFO", "INFO", True),
        ("DEBUG", "DEBUG", True),
        ("OFF", "WARNING", False),
    ],
)
def test_request_log_mode_controls_uvicorn_access_and_httpx_levels(
    tmp_path, request_log_mode, expected_level, expected_access_enabled
):
    """Request log mode should control request-heavy loggers and uvicorn access toggle."""
    settings = build_settings(tmp_path, request_log_mode=request_log_mode)
    log_config = build_logging_dict(settings, stderr_isatty=True)

    assert log_config["loggers"]["uvicorn.access"]["level"] == expected_level
    assert log_config["loggers"]["httpx"]["level"] == expected_level
    assert is_access_log_enabled(settings.request_log_mode) is expected_access_enabled


def test_log_use_colors_is_tty_safe(tmp_path, monkeypatch):
    """Color output should require both LOG_USE_COLORS and a TTY stream."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    settings = build_settings(tmp_path, log_use_colors=True)
    color_on_config = build_logging_dict(settings, stderr_isatty=True)
    color_off_notty_config = build_logging_dict(settings, stderr_isatty=False)

    no_color_settings = build_settings(tmp_path, log_use_colors=False)
    color_off_config = build_logging_dict(no_color_settings, stderr_isatty=True)

    assert color_on_config["formatters"]["standard"]["use_colors"] is True
    assert color_off_notty_config["formatters"]["standard"]["use_colors"] is False
    assert color_off_config["formatters"]["standard"]["use_colors"] is False


def test_no_color_env_overrides_log_use_colors(tmp_path, monkeypatch):
    """NO_COLOR env var should disable colors even when LOG_USE_COLORS is true."""
    monkeypatch.setenv("NO_COLOR", "")
    settings = build_settings(tmp_path, log_use_colors=True)
    config = build_logging_dict(settings, stderr_isatty=True)
    assert config["formatters"]["standard"]["use_colors"] is False


def test_color_level_formatter_colors_level_name_only():
    """Formatter should colorize level names and leave record state unchanged."""
    formatter = ColorLevelFormatter(fmt="%(levelname)s|%(message)s", use_colors=True)
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)
    assert output == "\x1b[32mINFO\x1b[0m|hello"
    assert record.levelname == "INFO"
