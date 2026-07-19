import runpy
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from sqlalchemy import MetaData

from app.db import Base


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


def test_alembic_target_metadata_uses_orm_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = Path(__file__).parents[1]
    config = SimpleNamespace(
        config_file_name=None,
        get_main_option=lambda _name: "",
        set_main_option=lambda _name, _value: None,
    )
    context = SimpleNamespace(
        config=config,
        is_offline_mode=lambda: True,
        configure=lambda **_kwargs: None,
        begin_transaction=nullcontext,
        run_migrations=lambda: None,
    )
    alembic = ModuleType("alembic")
    alembic.__dict__["context"] = context
    monkeypatch.setitem(sys.modules, "alembic", alembic)

    environment = runpy.run_path(str(backend / "migrations" / "env.py"))
    assert "target_metadata" in environment
    target_metadata = environment["target_metadata"]

    assert target_metadata is not None
    assert isinstance(target_metadata, MetaData)
    assert target_metadata.naming_convention == Base.metadata.naming_convention
    assert set(target_metadata.tables) == set(Base.metadata.tables)

    for table_name, expected_table in Base.metadata.tables.items():
        target_table = target_metadata.tables[table_name]
        target_columns = [
            (
                column.name,
                str(column.type),
                column.nullable,
                column.primary_key,
                tuple(sorted(foreign_key.target_fullname for foreign_key in column.foreign_keys)),
            )
            for column in target_table.columns
        ]
        expected_columns = [
            (
                column.name,
                str(column.type),
                column.nullable,
                column.primary_key,
                tuple(sorted(foreign_key.target_fullname for foreign_key in column.foreign_keys)),
            )
            for column in expected_table.columns
        ]
        target_constraints = sorted(
            (type(constraint).__name__, constraint.name) for constraint in target_table.constraints
        )
        expected_constraints = sorted(
            (type(constraint).__name__, constraint.name)
            for constraint in expected_table.constraints
        )
        target_indexes = sorted(
            (index.name, index.unique, tuple(column.name for column in index.columns))
            for index in target_table.indexes
        )
        expected_indexes = sorted(
            (index.name, index.unique, tuple(column.name for column in index.columns))
            for index in expected_table.indexes
        )

        assert target_columns == expected_columns
        assert target_constraints == expected_constraints
        assert target_indexes == expected_indexes
