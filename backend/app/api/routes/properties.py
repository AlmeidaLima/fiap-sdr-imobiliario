from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.database.property_repository import PropertyRepository
from app.database.session import get_db
from app.schemas.property import (
    PropertyResponse,
    PropertySearchResponse,
)
from app.schemas.property_search_intent import (
    PropertyNaturalLanguageSearchRequest,
)
from app.services.embedding_service import EmbeddingService
from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)
from app.services.property_natural_language_search_service import (
    PropertyNaturalLanguageSearchService,
)
from app.services.property_search_intent_service import (
    PropertySearchIntentService,
)
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


@router.get(
    "/semantic-search",
    response_model=list[PropertySearchResponse],
)
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
) -> list[PropertySearchResponse]:

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
        PropertySearchResponse(
            id=property_embedding.property.id,
            external_id=(
                property_embedding.property.external_id
            ),
            title=property_embedding.property.title,
            description=(
                property_embedding.property.description
            ),
            neighborhood=(
                property_embedding.property.neighborhood
            ),
            usable_area=(
                property_embedding.property.usable_area
            ),
            bedrooms=(
                property_embedding.property.bedrooms
            ),
            bathrooms=(
                property_embedding.property.bathrooms
            ),
            parking_spaces=(
                property_embedding.property.parking_spaces
            ),
            price=property_embedding.property.price,
            similarity_score=round(
                similarity_score,
                4,
            ),
        )
        for property_embedding, similarity_score in results
    ]


@router.get(
    "/hybrid-search",
    response_model=list[PropertySearchResponse],
)
def hybrid_search(
        q: str = Query(
            ...,
            min_length=3,
            description="Consulta em linguagem natural",
        ),
        neighborhood: str | None = Query(
            None,
            description="Bairro do imóvel",
        ),
        min_price: Decimal | None = Query(
            None,
            ge=0,
            description="Preço mínimo",
        ),
        max_price: Decimal | None = Query(
            None,
            ge=0,
            description="Preço máximo",
        ),
        min_bedrooms: int | None = Query(
            None,
            ge=0,
            description="Quantidade mínima de quartos",
        ),
        min_bathrooms: int | None = Query(
            None,
            ge=0,
            description="Quantidade mínima de banheiros",
        ),
        min_parking_spaces: int | None = Query(
            None,
            ge=0,
            description="Quantidade mínima de vagas",
        ),
        min_usable_area: int | None = Query(
            None,
            ge=0,
            description="Área útil mínima em m²",
        ),
        available: bool = Query(
            True,
            description="Disponibilidade do imóvel",
        ),
        limit: int = Query(
            5,
            ge=1,
            le=20,
            description="Quantidade máxima de resultados",
        ),
        db: Session = Depends(get_db),
) -> list[PropertySearchResponse]:

    repository = PropertyEmbeddingRepository(db)

    embedding_service = EmbeddingService()

    service = PropertyHybridSearchService(
        embedding_service=embedding_service,
        repository=repository,
    )

    results = service.search(
        query=q,
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

    return [
        PropertySearchResponse(
            id=property_embedding.property.id,
            external_id=(
                property_embedding.property.external_id
            ),
            title=property_embedding.property.title,
            description=(
                property_embedding.property.description
            ),
            neighborhood=(
                property_embedding.property.neighborhood
            ),
            usable_area=(
                property_embedding.property.usable_area
            ),
            bedrooms=(
                property_embedding.property.bedrooms
            ),
            bathrooms=(
                property_embedding.property.bathrooms
            ),
            parking_spaces=(
                property_embedding.property.parking_spaces
            ),
            price=property_embedding.property.price,
            similarity_score=round(
                similarity_score,
                4,
            ),
        )
        for property_embedding, similarity_score in results
    ]

@router.post("/natural-language-search")
def natural_language_search(
        request: PropertyNaturalLanguageSearchRequest,
        db: Session = Depends(get_db),
):
    repository = PropertyEmbeddingRepository(db)

    embedding_service = EmbeddingService()

    hybrid_search_service = PropertyHybridSearchService(
        embedding_service=embedding_service,
        repository=repository,
    )

    intent_service = PropertySearchIntentService()

    service = PropertyNaturalLanguageSearchService(
        intent_service=intent_service,
        hybrid_search_service=hybrid_search_service,
    )

    results = service.search(
        message=request.message,
        limit=request.limit,
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
            "parking_spaces": (
                result.property.parking_spaces
            ),
            "price": result.property.price,
            "similarity_score": round(
                similarity_score,
                4,
            ),
        }
        for result, similarity_score in results
    ]