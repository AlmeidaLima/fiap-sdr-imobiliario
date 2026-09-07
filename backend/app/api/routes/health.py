from fastapi import APIRouter

from app.schemas.error import ErrorResponse
from app.schemas.health import HealthResponse


router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Erro interno da aplicação",
        },
    },
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="agente-sdr-imobiliario-api",
    )