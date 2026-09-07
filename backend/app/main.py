from fastapi import FastAPI
from fastapi.exceptions import HTTPException

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.exceptions import ApplicationException
from app.core.handlers.application_exception import application_exception_handler
from app.core.handlers.http_exception import http_exception_handler
from fastapi.exceptions import HTTPException, RequestValidationError
from app.core.handlers.validation_exception import (
    validation_exception_handler,
)

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    ApplicationException,
    application_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.include_router(health_router)

app.include_router(
    api_router,
    prefix="/api/v1",
)