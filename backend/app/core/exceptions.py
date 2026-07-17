from http import HTTPStatus

from app.schemas.errors import ErrorDetail


class AppException(Exception):
    def __init__(
        self,
        *,
        code: str = "application_error",
        message: str = "The request could not be completed.",
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "The requested resource was not found.") -> None:
        super().__init__(
            code="resource_not_found",
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
        )
