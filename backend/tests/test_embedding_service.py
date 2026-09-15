from app.services.embedding_service import (
    EmbeddingService,
)


def test_embedding_has_expected_dimension():
    service = EmbeddingService()

    embedding = service.embed_document(
        "Apartamento com 3 quartos, academia e churrasqueira."
    )

    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(
        isinstance(value, float)
        for value in embedding
    )