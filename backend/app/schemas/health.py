from pydantic import BaseModel


class RootStatusData(BaseModel):
    name: str
    status: str


class RootStatusResponse(BaseModel):
    data: RootStatusData


class HealthData(BaseModel):
    status: str


class HealthResponse(BaseModel):
    data: HealthData
