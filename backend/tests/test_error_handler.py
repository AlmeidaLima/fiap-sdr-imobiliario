import asyncio

from fastapi import Request

from app.core.exceptions import ApplicationException
from app.core.handlers.application_exception import application_exception_handler


def test_application_exception_returns_standard_error():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
    )

    exception = ApplicationException(
        detail="Erro de teste",
        status_code=400,
    )

    response = asyncio.run(
        application_exception_handler(
            request,
            exception,
        )
    )

    assert response.status_code == 400
    assert response.body == (
        b'{"error":"application_error","detail":"Erro de teste"}'
    )