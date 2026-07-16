from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, dict[str, str]]:
    return {"data": {"status": "ok"}}
