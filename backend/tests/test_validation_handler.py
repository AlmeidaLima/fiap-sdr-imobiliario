import asyncio

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from app.core.handlers.validation_exception import (
    validation_exception_handler,
)


def test_validation_exception_returns_standard_error():
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [],
        }
    )

    exception = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("body", "name"),
                "msg": "Field required",
                "input": {},
            }
        ]
    )

    response = asyncio.run(
        validation_exception_handler(
            request,
            exception,
        )
    )

    assert response.status_code == 422
    assert b'"error":"validation_error"' in response.body