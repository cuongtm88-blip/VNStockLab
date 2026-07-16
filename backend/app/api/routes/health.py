from fastapi import APIRouter, status

from app.schemas.health import (
    HealthData,
    HealthResponse,
    RootStatusData,
    RootStatusResponse,
)

root_router = APIRouter(tags=["System"])
router = APIRouter(tags=["System"])


@root_router.get(
    "/",
    response_model=RootStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API status",
)
def root() -> RootStatusResponse:
    return RootStatusResponse(data=RootStatusData(name="VNStockLab API", status="running"))


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API health",
)
def health() -> HealthResponse:
    return HealthResponse(data=HealthData(status="ok"))
