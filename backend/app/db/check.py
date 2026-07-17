import asyncio

from app.core.settings import Settings
from app.db.engine import create_database_engine, dispose_database_engine
from app.db.health import check_database_connection


async def _check() -> bool:
    engine = create_database_engine(Settings())
    try:
        return await check_database_connection(engine)
    finally:
        await dispose_database_engine(engine)


def main() -> int:
    successful = asyncio.run(_check())
    print("Database connection successful." if successful else "Database connection failed.")
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
