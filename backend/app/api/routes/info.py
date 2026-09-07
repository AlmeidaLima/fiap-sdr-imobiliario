from fastapi import APIRouter

from app.core.config import settings
from app.schemas.error import ErrorResponse
from app.schemas.info import InfoResponse


router = APIRouter(
    prefix="/info",
    tags=["Info"],
)


@router.get(
    "",
    response_model=InfoResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Erro de aplicação",
        },
        422: {
            "model": ErrorResponse,
            "description": "Erro de validação",
        },
    },
)
def get_info() -> InfoResponse:
    return InfoResponse(
        name=settings.app_name,
        version=settings.app_version,
    )