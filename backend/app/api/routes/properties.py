from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.database.property_repository import PropertyRepository
from app.database.session import get_db
from app.schemas.property import PropertyResponse
from app.services.embedding_service import EmbeddingService
from app.services.property_semantic_search_service import (
    PropertySemanticSearchService,
)
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


@router.get("/semantic-search")
def semantic_search(
        q: str = Query(
            ...,
            min_length=3,
            description="Consulta em linguagem natural",
        ),
        limit: int = Query(
            5,
            ge=1,
            le=20,
            description="Quantidade máxima de resultados",
        ),
        db: Session = Depends(get_db),
):
    repository = PropertyEmbeddingRepository(db)

    embedding_service = EmbeddingService()

    service = PropertySemanticSearchService(
        embedding_service=embedding_service,
        repository=repository,
    )

    results = service.search(
        query=q,
        limit=limit,
    )

    return [
        {
            "id": result.property.id,
            "external_id": result.property.external_id,
            "title": result.property.title,
            "description": result.property.description,
            "neighborhood": result.property.neighborhood,
            "usable_area": result.property.usable_area,
            "bedrooms": result.property.bedrooms,
            "bathrooms": result.property.bathrooms,
            "parking_spaces": result.property.parking_spaces,
            "price": result.property.price,
            "similarity_score": round(
                similarity_score,
                4,
            ),
        }
        for result, similarity_score in results
    ]