from fastapi import APIRouter

from app.api.routes.appointments import (
    router as appointments_router,
)
from app.api.routes.conversations import (
    router as conversations_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.handoffs import (
    router as handoffs_router,
)
from app.api.routes.info import (
    router as info_router,
)
from app.api.routes.lead_follow_ups import (
    router as lead_follow_ups_router,
)
from app.api.routes.properties import (
    router as properties_router,
)


api_router = APIRouter()

api_router.include_router(appointments_router)
api_router.include_router(handoffs_router)
api_router.include_router(health_router)
api_router.include_router(info_router)
api_router.include_router(properties_router)
api_router.include_router(conversations_router)
api_router.include_router(lead_follow_ups_router)