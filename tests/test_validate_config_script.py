"""Tests for scripts/validate_config.py output contract."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from tests.helpers import build_settings
from worksection_mcp.config.settings import Settings


def _load_validate_config_module():
    """Load scripts/validate_config.py as a module for direct function testing."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "validate_config.py"
    spec = importlib.util.spec_from_file_location("validate_config_script_test", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load validate_config.py module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_config_summary_includes_new_logging_fields(monkeypatch, tmp_path, capsys):
    """Step 2 summary should include LOG_USE_COLORS and REQUEST_LOG_MODE values."""
    module = _load_validate_config_module()
    settings = build_settings(tmp_path)

    monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        Settings,
        "validate_external_resources",
        lambda _self: {
            "dns_resolution": "✓ ok",
            "token_storage_writable": "✓ ok",
            "file_cache_writable": "✓ ok",
            "ssl_cert_dir": "✓ ok",
        },
    )

    exit_code = module.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Log Use Colors:" in output
    assert "Request Log Mode:" in output
