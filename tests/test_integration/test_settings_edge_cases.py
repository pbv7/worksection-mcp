"""Tests for settings validator edge cases and external resource checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from worksection_mcp.config.settings import Settings


def _base_kwargs(tmp_path: Path) -> dict[str, Any]:
    return {
        "worksection_client_id": "test_client_id_12345",
        "worksection_client_secret": "test_client_secret_value_123456",
        "worksection_account_url": "https://test.worksection.com",
        "worksection_redirect_uri": "https://localhost:8080/oauth/callback",
        "token_storage_path": tmp_path / "tokens",
        "file_cache_path": tmp_path / "files",
    }


class TestURLParsingEdgeCases:
    """URL validators should reject structurally invalid URLs and hostnames."""

    def test_unparseable_url_rejected(self, tmp_path):
        """A URL that can't be parsed at all should raise a validation error."""
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_account_url"] = "not a url at all"
        with pytest.raises(ValidationError, match="Invalid URL scheme"):
            Settings.model_validate(kwargs)

    def test_no_hostname_in_url(self, tmp_path):
        """A URL with scheme but no hostname should be rejected."""
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_account_url"] = "https://"
        with pytest.raises(ValidationError, match="Missing hostname"):
            Settings.model_validate(kwargs)


class TestCredentialValidation:
    """Credential validators should reject empty and whitespace-only values."""

    def test_whitespace_only_client_id(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_client_id"] = "        "
        with pytest.raises(ValidationError):
            Settings.model_validate(kwargs)

    def test_whitespace_only_client_secret(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        whitespace_secret = " " * 20
        kwargs["worksection_client_secret"] = whitespace_secret
        with pytest.raises(ValidationError):
            Settings.model_validate(kwargs)


class TestRedirectURIValidation:
    """Redirect URI must use HTTPS unless hostname is localhost."""

    def test_http_non_localhost_rejected(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_redirect_uri"] = "http://example.com/oauth/callback"
        with pytest.raises(ValidationError, match="requires HTTPS"):
            Settings.model_validate(kwargs)


class TestScopeValidation:
    """Scope validator should reject empty and invalid scope strings."""

    def test_empty_scopes_rejected(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_scopes"] = ""
        with pytest.raises(ValidationError):
            Settings.model_validate(kwargs)

    def test_whitespace_only_scopes_rejected(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_scopes"] = "   ,  , "
        with pytest.raises(ValidationError):
            Settings.model_validate(kwargs)

    def test_administrative_scope_accepted(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        kwargs["worksection_scopes"] = "projects_read,administrative"
        settings = Settings.model_validate(kwargs)
        assert "administrative" in settings.scopes_list


class TestPortValidation:
    """Port and positive-integer validators should reject out-of-range values."""

    def test_zero_port_rejected(self, tmp_path):
        kwargs = _base_kwargs(tmp_path)
        kwargs["oauth_callback_port"] = 0
        with pytest.raises(ValidationError, match="must be between 1 and 65535"):
            Settings.model_validate(kwargs)


class TestExternalResourceEdgeCases:
    """validate_external_resources should handle hostname-less URLs and
    SSL directory creation failures gracefully."""

    def test_dns_check_with_no_hostname(self, tmp_path):
        """A URL with no extractable hostname should produce a clear error."""
        from tests.helpers import build_settings

        settings = build_settings(tmp_path)
        # Simulate a hostname-less URL by overriding after construction
        object.__setattr__(settings, "worksection_account_url", "https://")

        results = settings.validate_external_resources()
        assert "No hostname" in results["dns_resolution"]

    def test_ssl_cert_dir_permission_error(self, tmp_path, monkeypatch):
        """If the SSL cert directory can't be created, the check should report failure."""
        from tests.helpers import build_settings

        settings = build_settings(tmp_path)

        monkeypatch.setattr(
            "pathlib.Path.mkdir",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("denied")),
        )

        results = settings.validate_external_resources()
        assert results["ssl_cert_dir"].startswith("✗")
