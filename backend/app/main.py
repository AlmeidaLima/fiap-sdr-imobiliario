import logging

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ApplicationException
from app.core.handlers.application_exception import (
    application_exception_handler,
)
from app.core.handlers.http_exception import (
    http_exception_handler,
)
from app.core.handlers.validation_exception import (
    validation_exception_handler,
)
from app.core.observability import (
    RequestObservabilityMiddleware,
    configure_logging,
)


configure_logging("app")
logging.getLogger("uvicorn.access").disabled = True

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RequestObservabilityMiddleware,
    cors_origins=CORS_ORIGINS,
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


app.include_router(
    api_router,
    prefix="/api/v1",
)
