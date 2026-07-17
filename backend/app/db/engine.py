from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.settings import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        echo=settings.database_echo,
    )


async def dispose_database_engine(engine: AsyncEngine) -> None:
    await engine.dispose()
