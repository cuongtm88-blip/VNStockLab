from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from app.api.dependencies import SettingsDep
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import AppException, ResourceNotFoundError
from app.core.settings import get_settings
from app.main import app
from app.middleware.request_id import RequestIDMiddleware
from app.schemas.common import (
    CollectionResponse,
    PaginationMeta,
    ResponseMeta,
    SingleResourceResponse,
)


class ExampleData(BaseModel):
    value: str


def create_error_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(test_app)

    @test_app.get("/application-error")
    def application_error() -> None:
        raise AppException(code="test_error", message="Safe test error.", status_code=400)

    @test_app.get("/missing")
    def missing() -> None:
        raise ResourceNotFoundError()

    @test_app.get("/validated")
    def validated(count: int = Query(ge=1)) -> dict[str, int]:
        return {"count": count}

    @test_app.get("/unexpected")
    def unexpected() -> None:
        raise RuntimeError("private internal diagnostic")

    return test_app


def test_valid_correlation_id_is_preserved() -> None:
    correlation_id = uuid4()
    response = TestClient(app).get(
        "/api/v1/health", headers={"X-Correlation-ID": str(correlation_id)}
    )

    assert response.headers["X-Request-ID"] == str(correlation_id)
    assert response.json()["meta"]["request_id"] == str(correlation_id)


def test_invalid_correlation_id_generates_uuid() -> None:
    response = TestClient(app).get("/", headers={"X-Correlation-ID": "not-a-uuid"})
    request_id = response.headers["X-Request-ID"]

    assert UUID(request_id)
    assert request_id != "not-a-uuid"


def test_separate_requests_receive_separate_ids() -> None:
    client = TestClient(app)

    assert client.get("/").headers["X-Request-ID"] != client.get("/").headers["X-Request-ID"]


def test_single_resource_schema_serializes() -> None:
    request_id = uuid4()
    response = SingleResourceResponse[ExampleData](
        data=ExampleData(value="example"), meta=ResponseMeta(request_id=request_id)
    )

    assert response.model_dump(mode="json") == {
        "data": {"value": "example"},
        "meta": {"request_id": str(request_id)},
    }


def test_collection_schema_and_pagination_validation() -> None:
    response = CollectionResponse[ExampleData](
        data=[ExampleData(value="example")],
        pagination=PaginationMeta(page=1, page_size=20, total_items=1, total_pages=1),
        meta=ResponseMeta(request_id=uuid4()),
    )

    assert response.pagination.total_items == 1
    for values in (
        {"page": 0, "page_size": 20, "total_items": 0, "total_pages": 0},
        {"page": 1, "page_size": 0, "total_items": 0, "total_pages": 0},
        {"page": 1, "page_size": 20, "total_items": -1, "total_pages": 0},
        {"page": 1, "page_size": 20, "total_items": 0, "total_pages": -1},
    ):
        with pytest.raises(ValidationError):
            PaginationMeta(**values)


def test_app_exception_uses_standard_envelope() -> None:
    response = TestClient(create_error_app()).get("/application-error")

    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "test_error",
        "message": "Safe test error.",
        "details": [],
        "request_id": response.headers["X-Request-ID"],
    }


def test_resource_not_found_error() -> None:
    response = TestClient(create_error_app()).get("/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"


def test_validation_error_omits_raw_input() -> None:
    response = TestClient(create_error_app()).get("/validated?count=secret-value")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "validation_failed"
    assert body["error"]["details"][0]["field"] == "query.count"
    assert "secret-value" not in response.text


def test_unknown_route_uses_standard_envelope() -> None:
    response = TestClient(create_error_app()).get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_unexpected_error_is_safe() -> None:
    correlation_id = uuid4()
    response = TestClient(create_error_app(), raise_server_exceptions=False).get(
        "/unexpected", headers={"X-Correlation-ID": str(correlation_id)}
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["message"] == "An unexpected error occurred."
    assert "private internal diagnostic" not in response.text
    assert response.headers["X-Request-ID"] == str(correlation_id)
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_settings_dependency_alias_and_cache() -> None:
    assert SettingsDep is not None
    assert get_settings() is get_settings()
