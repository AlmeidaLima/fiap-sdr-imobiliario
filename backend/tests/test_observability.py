import asyncio
import io
import logging
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.exceptions import ApplicationException
from app.core.handlers.application_exception import application_exception_handler
from app.core.handlers.http_exception import http_exception_handler
from app.core.handlers.validation_exception import validation_exception_handler
from app.core.observability import (
    RequestObservabilityMiddleware,
    SafeKeyValueFormatter,
    configure_logging,
    get_request_id,
    resolve_request_id,
)


SENSITIVE_VALUE = "SEGREDO_TESTE_OBSERVABILIDADE"
AUDIT_SENSITIVE_VALUE = "SEGREDO_AUDITORIA_RNF006"
REQUEST_ID = "5f78dc65-e551-4ac8-8325-9b4e980c6f1f"
SECOND_REQUEST_ID = "6baf14b8-f542-4d6f-b239-fdddb55791ec"
CORS_ORIGIN = "http://localhost:3000"


def _build_test_app() -> FastAPI:
    application = FastAPI()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[CORS_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        RequestObservabilityMiddleware,
        cors_origins=[CORS_ORIGIN],
    )
    application.add_exception_handler(
        FastAPIHTTPException,
        http_exception_handler,
    )
    application.add_exception_handler(
        ApplicationException,
        application_exception_handler,
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    @application.get("/application-error")
    def application_error():
        raise ApplicationException(
            detail="Erro de negócio controlado.",
            status_code=400,
            error="controlled_error",
        )

    @application.get("/http-error")
    def http_error():
        raise HTTPException(status_code=404, detail="Não encontrado.")

    @application.get("/validation")
    def validation(value: int):
        return {"value": value}

    def fail_before_endpoint():
        raise RuntimeError(SENSITIVE_VALUE)

    @application.get(
        "/unexpected",
        dependencies=[Depends(fail_before_endpoint)],
    )
    def unexpected():
        return {"unexpected": False}

    @application.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    @application.get("/context")
    async def context():
        before = get_request_id()
        await asyncio.sleep(0.01)
        return {"before": before, "after": get_request_id()}

    router = APIRouter()

    @router.get("/resource")
    def prefixed_resource():
        return {"status": "ok"}

    application.include_router(router, prefix="/api/v1")

    return application


class ApplicationLogCapture:
    def __init__(self) -> None:
        self.logger = logging.getLogger("app")
        self.original_handlers = list(self.logger.handlers)
        self.original_level = self.logger.level
        self.original_propagate = self.logger.propagate
        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(SafeKeyValueFormatter())
        self.logger.handlers = [handler]
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def close(self) -> None:
        self.logger.handlers = self.original_handlers
        self.logger.setLevel(self.original_level)
        self.logger.propagate = self.original_propagate

    @property
    def text(self) -> str:
        return self.stream.getvalue()


def test_preserves_known_http_contracts_and_returns_request_id():
    client = TestClient(_build_test_app())
    request_id = REQUEST_ID

    application_error = client.get(
        "/application-error",
        headers={"X-Request-ID": request_id},
    )
    assert application_error.status_code == 400
    assert application_error.json() == {
        "error": "controlled_error",
        "detail": "Erro de negócio controlado.",
    }
    assert application_error.headers["X-Request-ID"] == request_id

    http_error = client.get("/http-error")
    assert http_error.status_code == 404
    assert http_error.json() == {
        "error": "http_error",
        "detail": "Não encontrado.",
    }
    assert http_error.headers["X-Request-ID"]

    validation = client.get("/validation", params={"value": "invalid"})
    assert validation.status_code == 422
    assert validation.json()["error"] == "validation_error"
    assert validation.headers["X-Request-ID"]


def test_unexpected_dependency_error_is_safe_and_preserves_cors():
    capture = ApplicationLogCapture()
    try:
        client = TestClient(_build_test_app())
        response = client.get(
            "/unexpected",
            headers={
                "Origin": "http://localhost:3000",
                "X-Request-ID": REQUEST_ID,
            },
        )
    finally:
        capture.close()

    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_server_error",
        "detail": "Erro interno da aplicação.",
    }
    assert response.headers["X-Request-ID"] == REQUEST_ID
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:3000"
    )
    assert "event=request_failed" in capture.text
    assert "route=/unexpected" in capture.text
    assert "error_type=RuntimeError" in capture.text
    assert SENSITIVE_VALUE not in capture.text
    assert get_request_id() is None


def test_request_logging_excludes_body_query_and_invalid_external_id():
    capture = ApplicationLogCapture()
    try:
        client = TestClient(_build_test_app())
        response = client.get(
            "/validation",
            params={"value": SENSITIVE_VALUE},
            headers={"X-Request-ID": "invalid request id"},
        )
    finally:
        capture.close()

    generated_request_id = response.headers["X-Request-ID"]
    assert generated_request_id != "invalid request id"
    assert resolve_request_id(generated_request_id) == generated_request_id
    assert "event=request_completed" in capture.text
    assert "route=/validation" in capture.text
    assert "status_code=422" in capture.text
    assert SENSITIVE_VALUE not in capture.text
    assert "invalid request id" not in capture.text


def test_health_returns_request_id_without_application_event():
    capture = ApplicationLogCapture()
    try:
        response = TestClient(_build_test_app()).get(
            "/api/v1/health",
            headers={"X-Request-ID": REQUEST_ID},
        )
    finally:
        capture.close()

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == REQUEST_ID
    assert capture.text == ""


def test_request_log_uses_normalized_route_with_router_prefix():
    capture = ApplicationLogCapture()
    try:
        response = TestClient(_build_test_app()).get("/api/v1/resource")
    finally:
        capture.close()

    assert response.status_code == 200
    assert "route=/api/v1/resource" in capture.text


def test_context_is_isolated_between_concurrent_requests_and_restored():
    application = _build_test_app()

    async def execute_requests():
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await asyncio.gather(
                client.get(
                    "/context",
                    headers={"X-Request-ID": REQUEST_ID},
                ),
                client.get(
                    "/context",
                    headers={"X-Request-ID": SECOND_REQUEST_ID},
                ),
            )

    first, second = asyncio.run(execute_requests())

    assert first.json() == {
        "before": REQUEST_ID,
        "after": REQUEST_ID,
    }
    assert second.json() == {
        "before": SECOND_REQUEST_ID,
        "after": SECOND_REQUEST_ID,
    }
    assert get_request_id() is None


def test_formatter_uses_allowlist_and_sanitizes_control_characters():
    formatter = SafeKeyValueFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="safe_event\ninjected",
        args=(),
        exc_info=(RuntimeError, RuntimeError(SENSITIVE_VALUE), None),
    )
    record.request_id = "safe-id\nforged fake=value"
    record.message_content = SENSITIVE_VALUE
    record.arbitrary_object = object()

    output = formatter.format(record)

    assert "event=safe_event_injected" in output
    assert "request_id=safe-id_forged_fake_value" in output
    assert SENSITIVE_VALUE not in output
    assert "message_content" not in output
    assert "arbitrary_object" not in output
    assert "Traceback" not in output
    assert "\n" not in output


def test_external_request_id_is_validated_and_canonicalized():
    client = TestClient(_build_test_app())

    preserved = client.get(
        "/context",
        headers={"X-Request-ID": REQUEST_ID},
    )
    alternative = client.get(
        "/context",
        headers={"X-Request-ID": "{5F78DC65E5514AC883259B4E980C6F1F}"},
    )

    assert preserved.headers["X-Request-ID"] == REQUEST_ID
    assert alternative.headers["X-Request-ID"] == REQUEST_ID


def test_arbitrary_external_request_id_is_replaced_and_not_logged():
    capture = ApplicationLogCapture()
    try:
        response = TestClient(_build_test_app()).get(
            "/context",
            headers={"X-Request-ID": AUDIT_SENSITIVE_VALUE},
        )
    finally:
        capture.close()

    generated = response.headers["X-Request-ID"]
    assert generated != AUDIT_SENSITIVE_VALUE
    assert str(UUID(generated)) == generated
    assert AUDIT_SENSITIVE_VALUE not in capture.text


def test_cors_preflight_has_request_id_without_losing_cors_headers():
    capture = ApplicationLogCapture()
    try:
        response = TestClient(_build_test_app()).options(
            "/api/v1/resource",
            headers={
                "Origin": CORS_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "X-Request-ID": REQUEST_ID,
            },
        )
    finally:
        capture.close()

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == REQUEST_ID
    assert response.headers["access-control-allow-origin"] == CORS_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    assert capture.text.count("event=request_completed") == 1
    assert "route=unmatched" in capture.text


def test_failure_after_response_start_is_logged_without_second_response():
    capture = ApplicationLogCapture()
    sent_messages = []

    async def failing_app(scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        })
        raise RuntimeError(AUDIT_SENSITIVE_VALUE)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent_messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/stream",
        "raw_path": b"/stream",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
        "root_path": "",
    }

    try:
        asyncio.run(
            RequestObservabilityMiddleware(failing_app)(scope, receive, send)
        )
    finally:
        capture.close()

    assert [message["type"] for message in sent_messages] == [
        "http.response.start"
    ]
    assert "event=request_failed" in capture.text
    assert "error_type=RuntimeError" in capture.text
    assert AUDIT_SENSITIVE_VALUE not in capture.text


def test_configure_logging_is_idempotent():
    logger_name = f"app.test.idempotent.{uuid4()}"
    stream = io.StringIO()

    logger = configure_logging(logger_name, stream=stream)
    logger = configure_logging(logger_name, stream=stream)
    logger.info("single_event")

    assert stream.getvalue().count("event=single_event") == 1
    assert len(logger.handlers) == 1


def test_uvicorn_access_log_is_disabled_to_avoid_query_string_exposure():
    import app.main  # noqa: F401

    assert logging.getLogger("uvicorn.access").disabled is True
