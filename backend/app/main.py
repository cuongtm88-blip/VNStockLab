from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.logging import configure_logging
from app.core.settings import get_settings

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/")
def root() -> dict[str, dict[str, str]]:
    return {
        "data": {
            "name": "VNStockLab API",
            "status": "running",
        }
    }


app.include_router(health_router, prefix=settings.api_v1_prefix)
