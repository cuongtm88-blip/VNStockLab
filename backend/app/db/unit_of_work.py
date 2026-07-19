from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession


class AsyncUnitOfWork:
    """Explicit transaction boundary around an injected async session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> "AsyncUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            await self.rollback()
        return False

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
