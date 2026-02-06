"""Additional validator and environment checks for Settings."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.helpers import build_settings
from worksection_mcp.config.settings import Settings, get_settings


def _base_kwargs(tmp_path) -> dict[str, Any]:
    """Base kwargs reused for direct Settings construction in validator tests."""
    return {
        "worksection_client_id": "test_client_id_12345",
        "worksection_client_secret": "test_client_secret_value_123456",
        "worksection_account_url": "https://test.worksection.com",
        "worksection_redirect_uri": "https://localhost:8080/oauth/callback",
        "token_storage_path": tmp_path / "tokens",
        "file_cache_path": tmp_path / "files",
    }


def test_account_url_and_redirect_uri_validators(tmp_path):
    """URL validators should reject malformed URL structures and schemes."""
    invalid_account_url = _base_kwargs(tmp_path)
    invalid_account_url["worksection_account_url"] = "ftp://test.worksection.com"
    with pytest.raises(ValidationError, match="Invalid URL scheme"):
        Settings.model_validate(invalid_account_url)

    missing_hostname = _base_kwargs(tmp_path)
    missing_hostname["worksection_account_url"] = "https://"
    with pytest.raises(ValidationError, match="Missing hostname"):
        Settings.model_validate(missing_hostname)

    invalid_redirect = _base_kwargs(tmp_path)
    invalid_redirect["worksection_redirect_uri"] = "http://example.com/oauth/callback"
    with pytest.raises(ValidationError, match="requires HTTPS"):
        Settings.model_validate(invalid_redirect)


def test_credentials_scope_port_and_positive_validators(tmp_path):
    """Field validators should enforce min lengths, scopes, port bounds and positivity."""
    short_id = _base_kwargs(tmp_path)
    short_id["worksection_client_id"] = "short"
    with pytest.raises(ValidationError, match="minimum 8"):
        Settings.model_validate(short_id)

    too_short_secret = "x" * 12
    short_secret = _base_kwargs(tmp_path)
    short_secret["worksection_client_secret"] = too_short_secret
    with pytest.raises(ValidationError, match="minimum 16"):
        Settings.model_validate(short_secret)

    invalid_scopes = _base_kwargs(tmp_path)
    invalid_scopes["worksection_scopes"] = "projects_read,invalid_scope"
    with pytest.raises(ValidationError, match="Invalid scopes"):
        Settings.model_validate(invalid_scopes)

    invalid_port = _base_kwargs(tmp_path)
    invalid_port["oauth_callback_port"] = 70000
    with pytest.raises(ValidationError, match="must be between 1 and 65535"):
        Settings.model_validate(invalid_port)

    invalid_file_size = _base_kwargs(tmp_path)
    invalid_file_size["max_file_size_mb"] = 0
    with pytest.raises(ValidationError, match="must be greater than 0"):
        Settings.model_validate(invalid_file_size)


def test_ssl_consistency_validator_and_path_conversion(tmp_path):
    """Model validators should enforce SSL/redirect consistency and normalize path values."""
    invalid_ssl_redirect = _base_kwargs(tmp_path)
    invalid_ssl_redirect["oauth_callback_use_ssl"] = True
    invalid_ssl_redirect["worksection_redirect_uri"] = "http://localhost:8080/oauth/callback"
    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings.model_validate(invalid_ssl_redirect)

    path_kwargs = _base_kwargs(tmp_path)
    path_kwargs["token_storage_path"] = str(tmp_path / "tokens-str")
    path_kwargs["file_cache_path"] = str(tmp_path / "files-str")
    settings = Settings.model_validate(path_kwargs)
    assert isinstance(settings.token_storage_path, Path)
    assert isinstance(settings.file_cache_path, Path)


def test_external_resource_validation_success_and_failures(monkeypatch, tmp_path):
    """validate_external_resources should report DNS and filesystem failures explicitly."""
    settings = build_settings(tmp_path)

    results_ok = settings.validate_external_resources()
    assert results_ok["token_storage_writable"].startswith("✓")
    assert results_ok["file_cache_writable"].startswith("✓")
    assert results_ok["ssl_cert_dir"].startswith("✓")

    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(socket.gaierror(-2, "fail")),
    )
    results_dns_fail = settings.validate_external_resources()
    assert results_dns_fail["dns_resolution"].startswith("✗ Cannot resolve")

    settings.token_storage_path = tmp_path / "no-token-write"
    settings.token_storage_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "pathlib.Path.touch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("blocked")),
    )
    results_write_fail = settings.validate_external_resources()
    assert results_write_fail["token_storage_writable"].startswith("✗ Cannot write")
    assert results_write_fail["file_cache_writable"].startswith("✗ Cannot write")


def test_cached_settings_singleton_behavior(monkeypatch, tmp_path):
    """get_settings should return cached instance until cache is explicitly cleared."""
    kwargs = _base_kwargs(tmp_path)
    monkeypatch.setenv("WORKSECTION_CLIENT_ID", kwargs["worksection_client_id"])
    monkeypatch.setenv("WORKSECTION_CLIENT_SECRET", kwargs["worksection_client_secret"])
    monkeypatch.setenv("WORKSECTION_ACCOUNT_URL", kwargs["worksection_account_url"])
    monkeypatch.setenv("WORKSECTION_REDIRECT_URI", kwargs["worksection_redirect_uri"])
    monkeypatch.setenv("TOKEN_STORAGE_PATH", str(kwargs["token_storage_path"]))
    monkeypatch.setenv("FILE_CACHE_PATH", str(kwargs["file_cache_path"]))

    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
