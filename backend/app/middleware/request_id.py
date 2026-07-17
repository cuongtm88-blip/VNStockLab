from uuid import UUID, uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.common.request_context import reset_request_id, set_request_id

REQUEST_ID_HEADER = b"x-request-id"


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._request_id_from_headers(scope) or uuid4()
        scope.setdefault("state", {})["request_id"] = request_id
        token = set_request_id(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers = [header for header in headers if header[0].lower() != REQUEST_ID_HEADER]
                headers.append((REQUEST_ID_HEADER, str(request_id).encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            reset_request_id(token)

    @staticmethod
    def _request_id_from_headers(scope: Scope) -> UUID | None:
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-correlation-id":
                try:
                    return UUID(value.decode("ascii"))
                except (UnicodeDecodeError, ValueError):
                    return None
        return None
