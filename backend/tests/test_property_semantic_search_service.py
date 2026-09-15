from unittest.mock import Mock

from app.services.property_semantic_search_service import (
    PropertySemanticSearchService,
)


def test_semantic_search_service_generates_embedding_and_searches_repository():

    embedding_service = Mock()
    repository = Mock()

    query_embedding = [0.1] * 384

    embedding_service.embed_query.return_value = (
        query_embedding
    )

    repository.search_similar.return_value = [
        ("resultado_1", 0.91),
        ("resultado_2", 0.82),
    ]

    service = PropertySemanticSearchService(
        embedding_service=embedding_service,
        repository=repository,
    )

    result = service.search(
        query="apartamento com academia",
        limit=2,
    )

    embedding_service.embed_query.assert_called_once_with(
        "apartamento com academia"
    )

    repository.search_similar.assert_called_once_with(
        query_embedding=query_embedding,
        limit=2,
    )

    assert result == [
        ("resultado_1", 0.91),
        ("resultado_2", 0.82),
    ]