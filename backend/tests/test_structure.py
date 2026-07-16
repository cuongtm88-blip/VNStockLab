import importlib.util

from app.api.router import api_router
from app.api.routes import health
from app.main import app
from app.schemas.health import (
    HealthData,
    HealthResponse,
    RootStatusData,
    RootStatusResponse,
)


def test_foundation_modules_and_schemas() -> None:
    assert health.router is not None
    assert (
        RootStatusResponse(data=RootStatusData(name="VNStockLab API", status="running")).data.status
        == "running"
    )
    assert HealthResponse(data=HealthData(status="ok")).data.status == "ok"


def test_old_health_module_no_longer_exists() -> None:
    assert importlib.util.find_spec("app.api.health") is None


def test_api_router_includes_health_route() -> None:
    assert str(api_router.url_path_for("health")) == "/health"


def test_openapi_schema_contains_system_paths() -> None:
    paths = app.openapi()["paths"]

    assert "/" in paths
    assert "/api/v1/health" in paths
