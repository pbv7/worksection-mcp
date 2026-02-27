#!/usr/bin/env python3
"""Configuration validation utility.

This script validates your Worksection MCP configuration without starting the server.
Useful for debugging configuration issues.

Usage:
    uv run python scripts/validate_config.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def get_settings():
    """Import and return application settings lazily after path bootstrapping."""
    from worksection_mcp.config import get_settings as _get_settings

    return _get_settings()


_ANSI_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}
_ANSI_BOLD = "\033[1m"
_ANSI_RESET = "\033[0m"


def _supports_color() -> bool:
    """Return whether stdout likely supports ANSI colors."""
    if os.getenv("NO_COLOR"):
        return False
    term = os.getenv("TERM", "")
    if term == "dumb":
        return False
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty and isatty())


_USE_COLOR = _supports_color()


def _style(message: str, *, color: str | None = None, bold: bool = False) -> str:
    """Apply ANSI style when color output is enabled."""
    if not _USE_COLOR:
        return message

    prefixes: list[str] = []
    if bold:
        prefixes.append(_ANSI_BOLD)
    if color:
        color_code = _ANSI_COLORS.get(color)
        if color_code:
            prefixes.append(color_code)

    if not prefixes:
        return message
    return f"{''.join(prefixes)}{message}{_ANSI_RESET}"


def out(message: str = "", *, color: str | None = None, bold: bool = False) -> None:
    """Write one line to stdout."""
    sys.stdout.write(f"{_style(message, color=color, bold=bold)}\n")


def main():
    """Validate configuration and print results."""
    out("=" * 70, color="cyan", bold=True)
    out("Worksection MCP Configuration Validator", color="cyan", bold=True)
    out("=" * 70, color="cyan", bold=True)
    out()

    try:
        # Load settings (Pydantic validators run automatically)
        out("Step 1: Loading and validating configuration from .env...", color="blue", bold=True)
        out("-" * 70, color="blue")
        settings = get_settings()
        out("✓ All Pydantic validation checks passed", color="green")
        out()

        # Print key configuration
        out("Step 2: Configuration Summary", color="blue", bold=True)
        out("-" * 70, color="blue")
        out(f"Account URL:          {settings.worksection_account_url}")
        out(f"API Base URL:         {settings.api_base_url}")
        out(f"OAuth2 URL:           {settings.oauth2_base_url}")
        out(f"Redirect URI:         {settings.worksection_redirect_uri}")
        out(
            f"Client ID:            {settings.worksection_client_id[:8]}..."
            if len(settings.worksection_client_id) > 8
            else settings.worksection_client_id
        )
        out(f"Client Secret:        {settings.worksection_client_secret[:4]}***")
        out(f"Scopes:               {', '.join(settings.scopes_list)}")
        out(f"Callback Host:        {settings.oauth_callback_host}")
        out(f"Callback Port:        {settings.oauth_callback_port}")
        out(f"Callback SSL:         {settings.oauth_callback_use_ssl}")
        out(f"Token Storage:        {settings.token_storage_path}")
        out(f"File Cache:           {settings.file_cache_path}")
        out(f"Max File Size:        {settings.max_file_size_mb} MB")
        out(f"Cache Retention:      {settings.file_cache_retention_hours} hours")
        out(f"MCP Server Name:      {settings.mcp_server_name}")
        out(f"MCP Transport:        {settings.mcp_transport}")
        out(f"MCP Server Port:      {settings.mcp_server_port}")
        out(f"Log Level:            {settings.log_level}")
        out(f"Log Use Colors:       {settings.log_use_colors}")
        out(f"Request Log Mode:     {settings.request_log_mode}")
        out(f"Environment:          {settings.environment}")
        out()

        # Run external resource validation
        out("Step 3: Checking External Resources", color="blue", bold=True)
        out("-" * 70, color="blue")
        results = settings.validate_external_resources()

        all_passed = True
        for key, result in results.items():
            line = f"{key:30s}: {result}"
            if result.startswith("✗"):
                out(line, color="red")
            elif result.startswith("✓"):
                out(line, color="green")
            else:
                out(line)
            if result.startswith("✗"):
                all_passed = False

        out()

        if all_passed:
            out("=" * 70, color="green", bold=True)
            out("✓ All validation checks passed!", color="green", bold=True)
            out("=" * 70, color="green", bold=True)
            out()
            out("Your configuration is complete and valid.")
            out()
            out("Start the server with:")
            out("  uv run worksection-mcp")
            out()
            return 0
        out("=" * 70, color="yellow", bold=True)
        out("✗ Some external resource checks failed", color="yellow", bold=True)
        out("=" * 70, color="yellow", bold=True)
        out()
        out("Configuration is valid, but there are environment issues.", color="yellow")
        out("Please fix the errors above before starting the server.")
        out()
        return 1

    except ValueError as e:
        # Pydantic validation error
        out("=" * 70, color="red", bold=True)
        out("✗ Configuration Validation Failed", color="red", bold=True)
        out("=" * 70, color="red", bold=True)
        out()
        out(str(e), color="red")
        out()
        out("Please fix the configuration errors in your .env file")
        out("See .env.example for reference")
        out()
        return 1

    except Exception as e:
        out("=" * 70, color="red", bold=True)
        out("✗ Unexpected Error", color="red", bold=True)
        out("=" * 70, color="red", bold=True)
        out()
        out(f"{type(e).__name__}: {e}", color="red")
        out()
        out("This may indicate a bug or system issue.")
        out()
        return 1


if __name__ == "__main__":
    sys.exit(main())
