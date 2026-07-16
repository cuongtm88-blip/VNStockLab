from pathlib import Path

import pytest

from app.core.settings import Settings, get_settings


def test_default_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in Settings.model_fields:
        monkeypatch.delenv(f"VNSTOCKLAB_{name.upper()}", raising=False)

    settings = Settings()

    assert settings.app_name == "VNStockLab API"
    assert settings.app_version == "1.0.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.log_level == "INFO"
    assert settings.allowed_hosts == ["localhost", "127.0.0.1"]


def test_prefixed_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VNSTOCKLAB_ENVIRONMENT", "production")
    monkeypatch.setenv("VNSTOCKLAB_DEBUG", "true")
    monkeypatch.setenv("VNSTOCKLAB_LOG_LEVEL", "ERROR")

    settings = Settings()

    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.log_level == "ERROR"


def test_allowed_hosts_json_is_parsed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VNSTOCKLAB_ALLOWED_HOSTS", '["api.example.com","localhost"]')

    settings = Settings()

    assert settings.allowed_hosts == ["api.example.com", "localhost"]


def test_cached_settings_can_be_cleared(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    monkeypatch.setenv("VNSTOCKLAB_APP_NAME", "Test API")
    first = get_settings()
    second = get_settings()

    assert first is second
    assert first.app_name == "Test API"

    get_settings.cache_clear()
    monkeypatch.setenv("VNSTOCKLAB_APP_NAME", "Changed API")
    assert get_settings().app_name == "Changed API"
    get_settings.cache_clear()
