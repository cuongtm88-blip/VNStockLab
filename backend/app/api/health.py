from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root() -> dict[str, dict[str, str]]:
    return {
        "data": {
            "name": "VNStockLab API",
            "status": "running",
        }
    }


@router.get("/api/v1/health")
def health() -> dict[str, dict[str, str]]:
    return {"data": {"status": "ok"}}
