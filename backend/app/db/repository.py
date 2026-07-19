import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import BaseModel


class AsyncRepository[ModelT: BaseModel]:
    """Minimal async persistence operations without transaction ownership."""

    def __init__(self, session: AsyncSession, model_type: type[ModelT]) -> None:
        self.session = session
        self.model_type = model_type

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model_type, entity_id)

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
