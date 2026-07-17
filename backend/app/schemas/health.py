from pydantic import BaseModel

from app.schemas.common import SingleResourceResponse


class RootStatusData(BaseModel):
    name: str
    status: str


class HealthData(BaseModel):
    status: str


class RootStatusResponse(SingleResourceResponse[RootStatusData]):
    pass


class HealthResponse(SingleResourceResponse[HealthData]):
    pass
