from app.schemas.conversation import ConversationState
from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)


class ConversationPropertySearchService:
    """
    Converte o estado acumulado da conversa
    em parâmetros para a busca híbrida de imóveis.
    """

    def __init__(
            self,
            hybrid_search_service: PropertyHybridSearchService,
    ):
        self.hybrid_search_service = hybrid_search_service

    def search(
            self,
            state: ConversationState,
            limit: int = 5,
    ):
        query = self._build_semantic_query(state)

        return self.hybrid_search_service.search(
            query=query,
            neighborhood=state.neighborhood,
            min_price=state.min_price,
            max_price=state.max_price,
            min_bedrooms=state.min_bedrooms,
            min_bathrooms=state.min_bathrooms,
            min_parking_spaces=state.min_parking_spaces,
            min_usable_area=state.min_usable_area,
            available=True,
            limit=limit,
        )

    @staticmethod
    def _build_semantic_query(
            state: ConversationState,
    ) -> str:
        if state.semantic_preferences:
            return " ".join(
                state.semantic_preferences
            )

        return "imóvel residencial"