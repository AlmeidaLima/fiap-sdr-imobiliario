from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.property_repository import PropertyRepository
from app.database.session import get_db
from app.schemas.property import PropertyResponse
from app.services.property_service import PropertyService


router = APIRouter(
    prefix="/properties",
    tags=["Properties"],
)


@router.get(
    "",
    response_model=list[PropertyResponse],
)
def search_properties(
        neighborhood: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_bedrooms: int | None = None,
        min_bathrooms: int | None = None,
        min_parking_spaces: int | None = None,
        min_usable_area: int | None = None,
        available: bool = True,
        limit: int = 20,
        db: Session = Depends(get_db),
) -> list[PropertyResponse]:

    repository = PropertyRepository(db)
    service = PropertyService(repository)

    return service.search(
        neighborhood=neighborhood,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        min_bathrooms=min_bathrooms,
        min_parking_spaces=min_parking_spaces,
        min_usable_area=min_usable_area,
        available=available,
        limit=limit,
    )