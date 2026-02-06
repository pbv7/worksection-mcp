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


def main():
    """Validate configuration and print results."""
    print("=" * 70)
    print("Worksection MCP Configuration Validator")
    print("=" * 70)
    print()

    try:
        # Load settings (Pydantic validators run automatically)
        print("Step 1: Loading and validating configuration from .env...")
        print("-" * 70)
        settings = get_settings()
        print("✓ All Pydantic validation checks passed")
        print()

        # Print key configuration
        print("Step 2: Configuration Summary")
        print("-" * 70)
        print(f"Account URL:          {settings.worksection_account_url}")
        print(f"API Base URL:         {settings.api_base_url}")
        print(f"OAuth2 URL:           {settings.oauth2_base_url}")
        print(f"Redirect URI:         {settings.worksection_redirect_uri}")
        print(
            f"Client ID:            {settings.worksection_client_id[:8]}..."
            if len(settings.worksection_client_id) > 8
            else settings.worksection_client_id
        )
        print(f"Client Secret:        {settings.worksection_client_secret[:4]}***")
        print(f"Scopes:               {', '.join(settings.scopes_list)}")
        print(f"Callback Host:        {settings.oauth_callback_host}")
        print(f"Callback Port:        {settings.oauth_callback_port}")
        print(f"Callback SSL:         {settings.oauth_callback_use_ssl}")
        print(f"Token Storage:        {settings.token_storage_path}")
        print(f"File Cache:           {settings.file_cache_path}")
        print(f"Max File Size:        {settings.max_file_size_mb} MB")
        print(f"Cache Retention:      {settings.file_cache_retention_hours} hours")
        print(f"MCP Server Name:      {settings.mcp_server_name}")
        print(f"MCP Transport:        {settings.mcp_transport}")
        print(f"MCP Server Port:      {settings.mcp_server_port}")
        print(f"Log Level:            {settings.log_level}")
        print(f"Environment:          {settings.environment}")
        print()

        # Run external resource validation
        print("Step 3: Checking External Resources")
        print("-" * 70)
        results = settings.validate_external_resources()

        all_passed = True
        for key, result in results.items():
            print(f"{key:30s}: {result}")
            if result.startswith("✗"):
                all_passed = False

        print()

        if all_passed:
            print("=" * 70)
            print("✓ All validation checks passed!")
            print("=" * 70)
            print()
            print("Your configuration is complete and valid.")
            print()
            print("Start the server with:")
            print("  uv run worksection-mcp")
            print()
            return 0
        else:
            print("=" * 70)
            print("✗ Some external resource checks failed")
            print("=" * 70)
            print()
            print("Configuration is valid, but there are environment issues.")
            print("Please fix the errors above before starting the server.")
            print()
            return 1

    except ValueError as e:
        # Pydantic validation error
        print("=" * 70)
        print("✗ Configuration Validation Failed")
        print("=" * 70)
        print()
        print(str(e))
        print()
        print("Please fix the configuration errors in your .env file")
        print("See .env.example for reference")
        print()
        return 1

    except Exception as e:
        print("=" * 70)
        print("✗ Unexpected Error")
        print("=" * 70)
        print()
        print(f"{type(e).__name__}: {e}")
        print()
        print("This may indicate a bug or system issue.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
