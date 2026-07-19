import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import DateTime, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import CallableColumnDefault

from app.db.base import Base, BaseModel
from app.db.repository import AsyncRepository
from app.db.unit_of_work import AsyncUnitOfWork


class ExampleModel(BaseModel):
    __tablename__ = "orm_foundation_examples"

    name: Mapped[str] = mapped_column(unique=True, index=True)


def test_metadata_has_deterministic_naming_convention() -> None:
    assert Base.metadata.naming_convention == {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
    table = Base.metadata.tables["orm_foundation_examples"]
    assert table.primary_key.name == "pk_orm_foundation_examples"


def test_uuid_primary_key_mapping() -> None:
    column = inspect(ExampleModel).columns.id

    assert isinstance(column.type, UUID)
    assert column.type.as_uuid is True
    assert column.primary_key is True
    assert column.nullable is False
    assert isinstance(column.default, CallableColumnDefault)
    assert column.default.is_callable is True


def test_timestamp_mapping() -> None:
    created_at = inspect(ExampleModel).columns.created_at
    updated_at = inspect(ExampleModel).columns.updated_at

    assert isinstance(created_at.type, DateTime)
    assert created_at.type.timezone is True
    assert created_at.nullable is False
    assert created_at.server_default is not None
    assert isinstance(updated_at.type, DateTime)
    assert updated_at.type.timezone is True
    assert updated_at.nullable is False
    assert updated_at.server_default is not None
    assert updated_at.onupdate is not None


def test_soft_delete_mapping() -> None:
    deleted_at = inspect(ExampleModel).columns.deleted_at

    assert isinstance(deleted_at.type, DateTime)
    assert deleted_at.type.timezone is True
    assert deleted_at.nullable is True
    assert deleted_at.default is None


def test_base_model_is_abstract_and_has_no_table() -> None:
    assert BaseModel.__abstract__ is True
    assert "__table__" not in BaseModel.__dict__
    assert "base_model" not in Base.metadata.tables


@pytest.mark.asyncio
async def test_repository_get_by_id_without_commit() -> None:
    entity_id = uuid.uuid4()
    entity = ExampleModel(name="example")
    session = MagicMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=entity)
    session.commit = AsyncMock()
    repository = AsyncRepository(session, ExampleModel)

    assert await repository.get_by_id(entity_id) is entity
    session.get.assert_awaited_once_with(ExampleModel, entity_id)
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_repository_add_without_commit() -> None:
    entity = ExampleModel(name="example")
    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    repository = AsyncRepository(session, ExampleModel)

    assert await repository.add(entity) is entity
    session.add.assert_called_once_with(entity)
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_repository_delete_without_commit() -> None:
    entity = ExampleModel(name="example")
    session = MagicMock(spec=AsyncSession)
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    repository = AsyncRepository(session, ExampleModel)

    await repository.delete(entity)

    session.delete.assert_awaited_once_with(entity)
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_unit_of_work_exposes_session_and_does_not_auto_commit() -> None:
    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    unit_of_work = AsyncUnitOfWork(session)

    async with unit_of_work as entered:
        assert entered is unit_of_work
        assert entered.session is session

    session.commit.assert_not_awaited()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_unit_of_work_commit_and_rollback() -> None:
    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    unit_of_work = AsyncUnitOfWork(session)

    await unit_of_work.commit()
    await unit_of_work.rollback()

    session.commit.assert_awaited_once()
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_and_preserves_exception() -> None:
    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    unit_of_work = AsyncUnitOfWork(session)

    with pytest.raises(RuntimeError, match="failure"):
        async with unit_of_work:
            raise RuntimeError("failure")

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_model_annotations_use_expected_python_types() -> None:
    assert ExampleModel.id.type.python_type is uuid.UUID
    assert ExampleModel.created_at.type.python_type is datetime
