from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    request_id = response.headers["X-Request-ID"]

    assert response.status_code == 200
    assert UUID(request_id)
    assert response.json() == {
        "data": {
            "name": "VNStockLab API",
            "status": "running",
        },
        "meta": {"request_id": request_id},
    }


def test_health() -> None:
    response = client.get("/api/v1/health")
    request_id = response.headers["X-Request-ID"]

    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok"},
        "meta": {"request_id": request_id},
    }
