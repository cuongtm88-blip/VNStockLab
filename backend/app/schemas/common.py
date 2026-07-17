from uuid import UUID

from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    request_id: UUID


class SingleResourceResponse[T](BaseModel):
    data: T
    meta: ResponseMeta


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class CollectionResponse[T](BaseModel):
    data: list[T]
    pagination: PaginationMeta
    meta: ResponseMeta
