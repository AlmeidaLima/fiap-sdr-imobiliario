from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)
from app.services.property_search_intent_service import (
    PropertySearchIntentService,
)


class PropertyNaturalLanguageSearchService:

    def __init__(
            self,
            intent_service: PropertySearchIntentService,
            hybrid_search_service: PropertyHybridSearchService,
    ):
        self.intent_service = intent_service
        self.hybrid_search_service = hybrid_search_service

    def search(
            self,
            message: str,
            limit: int = 5,
    ):
        intent = self.intent_service.parse(
            message
        )

        return self.hybrid_search_service.search(
            query=intent.semantic_query,
            neighborhood=intent.neighborhood,
            min_price=intent.min_price,
            max_price=intent.max_price,
            min_bedrooms=intent.min_bedrooms,
            min_bathrooms=intent.min_bathrooms,
            min_parking_spaces=(
                intent.min_parking_spaces
            ),
            min_usable_area=intent.min_usable_area,
            available=True,
            limit=limit,
        )