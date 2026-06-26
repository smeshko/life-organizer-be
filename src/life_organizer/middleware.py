"""HTTP middleware for request/response logging and error capture."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from life_organizer.logging_config import get_logger

logger = get_logger("life_organizer.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log one line per HTTP request with method, path, status, and duration.

    Unhandled exceptions are logged with a full traceback and converted to a
    500 response so failures are captured in the logs instead of being silently
    swallowed by the ASGI server.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process a request, timing it and logging the outcome.

        Args:
            request: Incoming HTTP request.
            call_next: Downstream handler.

        Returns:
            The downstream response, or a 500 JSON response on unhandled error.
        """
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        client = request.client.host if request.client else "-"
        # Health probes fire every 30s from Docker; logging them buries real
        # traffic. Process them normally, just don't emit a log line.
        skip_log = request.url.path.endswith("/health")
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s -> 500 (%.1fms) client=%s request_id=%s",
                request.method,
                request.url.path,
                duration_ms,
                client,
                request_id,
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id},
                headers={"x-request-id": request_id},
            )

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = request_id
        if skip_log:
            return response
        # 5xx -> error, 4xx -> warning, else -> info
        if response.status_code >= 500:
            log = logger.error
        elif response.status_code >= 400:
            log = logger.warning
        else:
            log = logger.info
        log(
            "%s %s -> %d (%.1fms) client=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client,
            request_id,
        )
        return response
