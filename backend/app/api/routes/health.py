from fastapi import APIRouter, status

from app.common.request_context import get_request_id
from app.schemas.common import ResponseMeta
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
    return RootStatusResponse(
        data=RootStatusData(name="VNStockLab API", status="running"),
        meta=ResponseMeta(request_id=get_request_id()),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API health",
)
def health() -> HealthResponse:
    return HealthResponse(
        data=HealthData(status="ok"),
        meta=ResponseMeta(request_id=get_request_id()),
    )
