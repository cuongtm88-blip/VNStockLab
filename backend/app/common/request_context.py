from contextvars import ContextVar, Token
from uuid import UUID, uuid4

_request_id: ContextVar[UUID | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: UUID) -> Token[UUID | None]:
    return _request_id.set(request_id)


def get_request_id() -> UUID:
    request_id = _request_id.get()
    if request_id is None:
        request_id = uuid4()
        _request_id.set(request_id)
    return request_id


def reset_request_id(token: Token[UUID | None]) -> None:
    _request_id.reset(token)
