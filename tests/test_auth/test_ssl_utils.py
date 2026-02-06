"""Tests for SSL certificate utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from worksection_mcp.auth.ssl_utils import (
    create_ssl_context,
    ensure_ssl_cert,
    generate_self_signed_cert,
    is_cert_valid,
)


def test_generate_self_signed_cert_and_validate(tmp_path):
    """Generated cert/key pair should be readable and considered valid."""
    cert_path = tmp_path / "callback.crt"
    key_path = tmp_path / "callback.key"

    generate_self_signed_cert(cert_path, key_path, days=30, hostname="localhost")

    assert cert_path.exists()
    assert key_path.exists()
    assert is_cert_valid(cert_path, min_days_remaining=1) is True


def test_is_cert_valid_returns_false_for_missing_or_invalid_cert(tmp_path):
    """Missing and malformed cert files should be treated as invalid."""
    cert_path = tmp_path / "missing.crt"
    assert is_cert_valid(cert_path) is False

    cert_path.write_text("not a certificate")
    assert is_cert_valid(cert_path) is False


def test_ensure_ssl_cert_regenerates_only_when_needed(monkeypatch, tmp_path):
    """ensure_ssl_cert should call generator only if current cert is invalid."""
    cert_path = tmp_path / "callback.crt"
    key_path = tmp_path / "callback.key"

    generator = MagicMock()
    monkeypatch.setattr("worksection_mcp.auth.ssl_utils.generate_self_signed_cert", generator)
    monkeypatch.setattr(
        "worksection_mcp.auth.ssl_utils.is_cert_valid", lambda *_args, **_kwargs: True
    )
    ensure_ssl_cert(cert_path, key_path, days=7, hostname="localhost")
    generator.assert_not_called()

    monkeypatch.setattr(
        "worksection_mcp.auth.ssl_utils.is_cert_valid", lambda *_args, **_kwargs: False
    )
    ensure_ssl_cert(cert_path, key_path, days=7, hostname="localhost")
    generator.assert_called_once_with(cert_path, key_path, 7, "localhost")


def test_create_ssl_context_loads_generated_cert_chain(tmp_path):
    """create_ssl_context should load generated PEM files without errors."""
    cert_path = Path(tmp_path / "callback.crt")
    key_path = Path(tmp_path / "callback.key")
    generate_self_signed_cert(cert_path, key_path, days=30, hostname="localhost")

    context = create_ssl_context(cert_path, key_path)
    assert context is not None
