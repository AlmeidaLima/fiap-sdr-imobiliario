import logging
import re
import sys
from contextvars import ContextVar, Token
from time import monotonic
from collections.abc import Collection
from typing import Any, TextIO
from uuid import UUID, uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = "X-Request-ID"
API_PREFIX = "/api/v1"
HEALTH_ROUTE = "/api/v1/health"
MAX_FIELD_LENGTH = 128
SAFE_LOG_FIELDS = (
    "request_id",
    "method",
    "route",
    "status_code",
    "duration_ms",
    "error_type",
    "conversation_id",
    "qualified",
    "property_count",
    "follow_up_id",
    "lead_id",
    "attempt_number",
    "status",
    "interval_seconds",
    "batch_size",
    "processed",
    "delivered",
    "skipped",
    "failed",
)

_request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id_context.get()


def set_request_id(request_id: str) -> Token:
    return _request_id_context.set(request_id)


def reset_request_id(token: Token) -> None:
    _request_id_context.reset(token)


def resolve_request_id(candidate: str | None) -> str:
    if candidate:
        try:
            return str(UUID(candidate))
        except (ValueError, AttributeError):
            pass
    return str(uuid4())


def _safe_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if not isinstance(value, (str, int, float)):
        return None

    sanitized = re.sub(
        r"[^A-Za-z0-9._:/{}-]+",
        "_",
        str(value),
    )
    return sanitized[:MAX_FIELD_LENGTH]


class SafeKeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
        event = _safe_value(record.msg) or "unknown_event"
        parts = [
            timestamp,
            record.levelname,
            record.name,
            f"event={event}",
        ]

        for field in SAFE_LOG_FIELDS:
            value = getattr(record, field, None)
            if field == "request_id" and value is None:
                value = get_request_id()
            safe_value = _safe_value(value)
            if safe_value is not None:
                parts.append(f"{field}={safe_value}")

        return " ".join(parts)


def configure_logging(
        logger_name: str,
        stream: TextIO | None = None,
) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "_sdr_observability_handler", False):
            logger.removeHandler(handler)

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(SafeKeyValueFormatter())
    handler._sdr_observability_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    return logger


def _route_template(scope: Scope) -> str:
    route = scope.get("route")
    route_path = getattr(route, "path", None)
    request_path = scope.get("path", "")
    if (
        isinstance(route_path, str)
        and request_path.startswith(f"{API_PREFIX}/")
        and not route_path.startswith(f"{API_PREFIX}/")
    ):
        route_path = f"{API_PREFIX}{route_path}"
    safe_route = _safe_value(route_path)
    return safe_route or "unmatched"


class RequestObservabilityMiddleware:
    def __init__(
            self,
            app: ASGIApp,
            cors_origins: Collection[str] = (),
    ) -> None:
        self.app = app
        self.cors_origins = frozenset(cors_origins)
        self.logger = logging.getLogger("app.observability")

    async def __call__(
            self,
            scope: Scope,
            receive: Receive,
            send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = resolve_request_id(headers.get(REQUEST_ID_HEADER))
        scope.setdefault("state", {})["request_id"] = request_id
        token = set_request_id(request_id)
        started = monotonic()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            try:
                await self.app(scope, receive, send_with_request_id)
            except Exception as exc:
                self._log_failed(
                    scope=scope,
                    request_id=request_id,
                    status_code=500,
                    started=started,
                    error_type=type(exc).__name__,
                )
                if response_started:
                    return

                response_headers = {REQUEST_ID_HEADER: request_id}
                origin = headers.get("origin")
                if origin in self.cors_origins:
                    response_headers.update({
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Vary": "Origin",
                    })

                response = JSONResponse(
                    status_code=500,
                    content={
                        "error": "internal_server_error",
                        "detail": "Erro interno da aplicação.",
                    },
                    headers=response_headers,
                )
                await response(scope, receive, send)
                return

            route = _route_template(scope)
            if route == HEALTH_ROUTE:
                return

            duration_ms = round((monotonic() - started) * 1000)
            event = "request_failed" if status_code >= 500 else "request_completed"
            level = logging.ERROR if status_code >= 500 else logging.INFO
            self.logger.log(
                level,
                event,
                extra={
                    "request_id": request_id,
                    "method": scope.get("method", "UNKNOWN"),
                    "route": route,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
        finally:
            reset_request_id(token)

    def _log_failed(
            self,
            scope: Scope,
            request_id: str,
            status_code: int,
            started: float,
            error_type: str,
    ) -> None:
        self.logger.error(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": scope.get("method", "UNKNOWN"),
                "route": _route_template(scope),
                "status_code": status_code,
                "duration_ms": round((monotonic() - started) * 1000),
                "error_type": error_type,
            },
        )
