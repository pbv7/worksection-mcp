"""Centralized logging configuration for Worksection MCP server."""

from __future__ import annotations

import logging
import logging.config
import sys
from typing import TYPE_CHECKING, Any, ClassVar, Literal

if TYPE_CHECKING:
    from worksection_mcp.config.settings import Settings


class ColorLevelFormatter(logging.Formatter):
    """Formatter that applies ANSI color codes to level names only."""

    RESET = "\x1b[0m"
    LEVEL_COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\x1b[36m",  # cyan
        logging.INFO: "\x1b[32m",  # green
        logging.WARNING: "\x1b[33m",  # yellow
        logging.ERROR: "\x1b[31m",  # red
        logging.CRITICAL: "\x1b[1;31m",  # bold red
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool = False,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record and colorize level name when enabled."""
        if not self.use_colors:
            return super().format(record)

        original_levelname = record.levelname
        color = self.LEVEL_COLORS.get(record.levelno)
        if color:
            record.levelname = f"{color}{original_levelname}{self.RESET}"

        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def _should_use_colors(settings: Settings, stderr_isatty: bool | None = None) -> bool:
    if not settings.log_use_colors:
        return False

    if stderr_isatty is not None:
        return stderr_isatty

    isatty = getattr(sys.stderr, "isatty", None)
    return bool(isatty and isatty())


def _request_logger_level(request_log_mode: str) -> str:
    if request_log_mode == "DEBUG":
        return "DEBUG"
    if request_log_mode == "OFF":
        return "WARNING"
    return "INFO"


def _uvicorn_access_enabled(request_log_mode: str) -> bool:
    return request_log_mode != "OFF"


def build_logging_dict(settings: Settings, stderr_isatty: bool | None = None) -> dict[str, Any]:
    """Build logging dictConfig used by app loggers and Uvicorn."""
    use_colors = _should_use_colors(settings, stderr_isatty=stderr_isatty)
    request_logger_level = _request_logger_level(settings.request_log_mode)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": "worksection_mcp.logging_config.ColorLevelFormatter",
                "fmt": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "use_colors": use_colors,
            }
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "standard",
            }
        },
        # Root handler is intentional: catches third-party loggers not
        # explicitly listed below.  Named loggers use propagate=False so
        # messages are never emitted twice.
        "root": {
            "handlers": ["stderr"],
            "level": settings.log_level,
        },
        "loggers": {
            "worksection_mcp": {
                "handlers": ["stderr"],
                "level": settings.log_level,
                "propagate": False,
            },
            "fastmcp": {
                "handlers": ["stderr"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["stderr"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["stderr"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["stderr"],
                "level": request_logger_level,
                "propagate": False,
            },
            "httpx": {
                "handlers": ["stderr"],
                "level": request_logger_level,
                "propagate": False,
            },
        },
    }


def configure_logging(settings: Settings, stderr_isatty: bool | None = None) -> dict[str, Any]:
    """Apply centralized logging configuration and return used dictConfig."""
    log_config = build_logging_dict(settings, stderr_isatty=stderr_isatty)
    logging.config.dictConfig(log_config)
    return log_config


def is_access_log_enabled(request_log_mode: str) -> bool:
    """Expose Uvicorn access-log toggle mapping."""
    return _uvicorn_access_enabled(request_log_mode)
