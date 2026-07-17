from pathlib import Path


def test_alembic_foundation_files_exist() -> None:
    backend = Path(__file__).parents[1]
    expected = (
        backend / "alembic.ini",
        backend / "migrations" / "env.py",
        backend / "migrations" / "script.py.mako",
        backend / "migrations" / "README",
        backend / "migrations" / "versions" / ".gitkeep",
    )

    assert all(path.exists() for path in expected)


def test_alembic_uses_application_settings_without_hard_coded_password() -> None:
    backend = Path(__file__).parents[1]
    ini = (backend / "alembic.ini").read_text()
    environment = (backend / "migrations" / "env.py").read_text()

    assert "change-me-local-only" not in ini
    assert "sqlalchemy.url =" in ini
    assert "Settings().database_url" in environment
