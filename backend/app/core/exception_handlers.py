import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.common.request_context import get_request_id
from app.core.exceptions import AppException
from app.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES: dict[int, str] = {
    HTTPStatus.BAD_REQUEST: "invalid_request",
    HTTPStatus.UNAUTHORIZED: "authentication_required",
    HTTPStatus.FORBIDDEN: "permission_denied",
    HTTPStatus.NOT_FOUND: "resource_not_found",
    HTTPStatus.METHOD_NOT_ALLOWED: "method_not_allowed",
    HTTPStatus.CONFLICT: "resource_conflict",
    HTTPStatus.UNSUPPORTED_MEDIA_TYPE: "unsupported_media_type",
    HTTPStatus.TOO_MANY_REQUESTS: "rate_limit_exceeded",
}


def _error_response(
    *,
    request_id: UUID,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    content = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
        headers={"X-Request-ID": str(request_id)},
    )


def _request_id(request: Request) -> UUID:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, UUID) else get_request_id()


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _error_response(
        request_id=_request_id(request),
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            code=str(error["type"]),
            message=str(error["msg"]),
        )
        for error in exc.errors()
    ]
    return _error_response(
        request_id=_request_id(request),
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="validation_failed",
        message="Request validation failed.",
        details=details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "The HTTP request failed."
    return _error_response(
        request_id=_request_id(request),
        status_code=exc.status_code,
        code=HTTP_ERROR_CODES.get(exc.status_code, "http_error"),
        message=message,
    )


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _request_id(request)
    logger.exception("Unexpected request failure; request_id=%s", request_id, exc_info=exc)
    return _error_response(
        request_id=request_id,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="internal_error",
        message="An unexpected error occurred.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_exception_handler)
