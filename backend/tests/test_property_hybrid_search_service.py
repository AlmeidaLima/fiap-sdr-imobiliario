from decimal import Decimal
from unittest.mock import Mock

from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)


def test_hybrid_search_service_generates_embedding_and_applies_filters():
    embedding_service = Mock()
    repository = Mock()

    query_embedding = [0.1, 0.2, 0.3]

    embedding_service.embed_query.return_value = (
        query_embedding
    )

    repository.search_similar_with_filters.return_value = []

    service = PropertyHybridSearchService(
        embedding_service=embedding_service,
        repository=repository,
    )

    result = service.search(
        query="apartamento com boa área de lazer",
        neighborhood="Boa Vista",
        max_price=Decimal("700000.00"),
        min_bedrooms=3,
        min_bathrooms=2,
        min_parking_spaces=1,
        min_usable_area=70,
        available=True,
        limit=5,
    )

    embedding_service.embed_query.assert_called_once_with(
        "apartamento com boa área de lazer"
    )

    repository.search_similar_with_filters.assert_called_once_with(
        query_embedding=query_embedding,
        neighborhood="Boa Vista",
        min_price=None,
        max_price=Decimal("700000.00"),
        min_bedrooms=3,
        min_bathrooms=2,
        min_parking_spaces=1,
        min_usable_area=70,
        available=True,
        limit=5,
    )

    assert result == []