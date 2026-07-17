import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.db.engine import create_database_engine, dispose_database_engine
from app.db.health import check_database_connection
from app.db.session import create_session_factory, get_database_session
from app.main import app


def test_database_settings_defaults_and_safe_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in Settings.model_fields:
        if name.startswith("database_"):
            monkeypatch.delenv(f"VNSTOCKLAB_{name.upper()}", raising=False)
    settings = Settings()

    assert settings.database_host == "localhost"
    assert settings.database_port == 5432
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert settings.database_pool_timeout_seconds == 30
    assert settings.database_url.drivername == "postgresql+psycopg"
    assert "change-me-local-only" not in repr(settings)
    assert "change-me-local-only" not in str(settings.database_url)


def test_database_settings_environment_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VNSTOCKLAB_DATABASE_HOST", "database.example")
    monkeypatch.setenv("VNSTOCKLAB_DATABASE_PORT", "6543")
    monkeypatch.setenv("VNSTOCKLAB_DATABASE_PASSWORD", "p@ss/word")
    settings = Settings()

    assert settings.database_host == "database.example"
    assert settings.database_port == 6543
    assert settings.database_url.host == "database.example"
    assert settings.database_url.port == 6543
    assert "p%40ss%2Fword" in settings.database_url.render_as_string(hide_password=False)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("database_port", 0),
        ("database_port", 65536),
        ("database_pool_size", 0),
        ("database_max_overflow", -1),
        ("database_pool_timeout_seconds", 0),
    ],
)
def test_invalid_database_settings(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field: value})  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_engine_and_session_factory_require_no_connection() -> None:
    engine = create_database_engine(Settings())
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        factory = create_session_factory(engine)
        assert factory.kw["expire_on_commit"] is False
        assert factory.kw["autoflush"] is False
    finally:
        await dispose_database_engine(engine)


@pytest.mark.asyncio
async def test_session_dependency_rolls_back_and_closes_without_commit() -> None:
    session = MagicMock(spec=AsyncSession)
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.commit = AsyncMock()
    factory = MagicMock(spec=async_sessionmaker)
    factory.return_value = session
    test_app = FastAPI()
    test_app.state.database_session_factory = factory
    request = Request({"type": "http", "app": test_app})
    dependency: AsyncGenerator[AsyncSession] = get_database_session(request)

    assert await anext(dependency) is session
    with pytest.raises(RuntimeError, match="failure"):
        await dependency.athrow(RuntimeError("failure"))

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_database_health_success() -> None:
    connection = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = connection
    engine = MagicMock()
    engine.connect.return_value = context_manager

    assert await check_database_connection(engine) is True
    connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_database_health_failure_is_safe(caplog: pytest.LogCaptureFixture) -> None:
    password = "highly-secret-password"
    context_manager = AsyncMock()
    context_manager.__aenter__.side_effect = OperationalError("statement", {}, Exception(password))
    engine = MagicMock()
    engine.connect.return_value = context_manager

    with caplog.at_level(logging.WARNING):
        assert await check_database_connection(engine) is False
    assert password not in caplog.text


def test_application_lifespan_manages_database_state() -> None:
    from fastapi.testclient import TestClient

    with TestClient(app):
        assert app.state.database_engine.dialect.name == "postgresql"
        assert isinstance(app.state.database_session_factory, async_sessionmaker)
