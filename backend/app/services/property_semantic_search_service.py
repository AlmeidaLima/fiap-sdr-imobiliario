from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.models.property_embedding import PropertyEmbedding
from app.services.embedding_service import EmbeddingService


class PropertySemanticSearchService:

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
            limit: int = 5,
    ) -> list[tuple[PropertyEmbedding, float]]:
        query_embedding = self.embedding_service.embed_query(
            query
        )

        return self.repository.search_similar(
            query_embedding=query_embedding,
            limit=limit,
        )