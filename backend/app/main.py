from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.api.routes.health import root_router
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.engine import create_database_engine, dispose_database_engine
from app.db.session import create_session_factory
from app.middleware.request_id import RequestIDMiddleware

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    engine = create_database_engine(settings)
    application.state.database_engine = engine
    application.state.database_session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await dispose_database_engine(engine)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)

app.include_router(root_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
