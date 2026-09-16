from decimal import Decimal

from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.services.embedding_service import EmbeddingService


class PropertyHybridSearchService:

    def __init__(
            self,
            embedding_service: EmbeddingService,
            repository: PropertyEmbeddingRepository,
    ):
        self.embedding_service = embedding_service
        self.repository = repository

    def search(
            self,
            query: str,
            neighborhood: str | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            min_bedrooms: int | None = None,
            min_bathrooms: int | None = None,
            min_parking_spaces: int | None = None,
            min_usable_area: int | None = None,
            available: bool = True,
            limit: int = 5,
    ):
        query_embedding = (
            self.embedding_service.embed_query(
                query
            )
        )

        return (
            self.repository.search_similar_with_filters(
                query_embedding=query_embedding,
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
        )