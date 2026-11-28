import logging
import re
import time
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._get_request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id

        method = scope.get("method", "")
        path = scope.get("path", "")
        started_at = time.perf_counter()
        status_code: int | None = None

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-Id"] = request_id

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "event": "request_failed",
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": self._elapsed_ms(started_at),
                },
            )
            raise
        else:
            logger.info(
                "request_completed",
                extra={
                    "event": "request_completed",
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": self._elapsed_ms(started_at),
                },
            )

    @staticmethod
    def _get_request_id(scope: Scope) -> str:
        candidate = Headers(scope=scope).get("x-request-id", "")
        if REQUEST_ID_PATTERN.fullmatch(candidate):
            return candidate
        return str(uuid4())

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000, 2)
