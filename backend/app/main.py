from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="VNStockLab API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(health_router)
