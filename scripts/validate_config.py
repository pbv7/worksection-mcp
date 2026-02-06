#!/usr/bin/env python3
"""Configuration validation utility.

This script validates your Worksection MCP configuration without starting the server.
Useful for debugging configuration issues.

Usage:
    uv run python scripts/validate_config.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from worksection_mcp.config import get_settings


def out(message: str = "") -> None:
    """Write one line to stdout."""
    sys.stdout.write(f"{message}\n")


def main():
    """Validate configuration and print results."""
    out("=" * 70)
    out("Worksection MCP Configuration Validator")
    out("=" * 70)
    out()

    try:
        # Load settings (Pydantic validators run automatically)
        out("Step 1: Loading and validating configuration from .env...")
        out("-" * 70)
        settings = get_settings()
        out("✓ All Pydantic validation checks passed")
        out()

        # Print key configuration
        out("Step 2: Configuration Summary")
        out("-" * 70)
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
        out(f"Environment:          {settings.environment}")
        out()

        # Run external resource validation
        out("Step 3: Checking External Resources")
        out("-" * 70)
        results = settings.validate_external_resources()

        all_passed = True
        for key, result in results.items():
            out(f"{key:30s}: {result}")
            if result.startswith("✗"):
                all_passed = False

        out()

        if all_passed:
            out("=" * 70)
            out("✓ All validation checks passed!")
            out("=" * 70)
            out()
            out("Your configuration is complete and valid.")
            out()
            out("Start the server with:")
            out("  uv run worksection-mcp")
            out()
            return 0
        out("=" * 70)
        out("✗ Some external resource checks failed")
        out("=" * 70)
        out()
        out("Configuration is valid, but there are environment issues.")
        out("Please fix the errors above before starting the server.")
        out()
        return 1

    except ValueError as e:
        # Pydantic validation error
        out("=" * 70)
        out("✗ Configuration Validation Failed")
        out("=" * 70)
        out()
        out(str(e))
        out()
        out("Please fix the configuration errors in your .env file")
        out("See .env.example for reference")
        out()
        return 1

    except Exception as e:
        out("=" * 70)
        out("✗ Unexpected Error")
        out("=" * 70)
        out()
        out(f"{type(e).__name__}: {e}")
        out()
        out("This may indicate a bug or system issue.")
        out()
        return 1


if __name__ == "__main__":
    sys.exit(main())
