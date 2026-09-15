from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.database.session import SessionLocal
from app.models.property import Property
from app.models.property_embedding import PropertyEmbedding
from app.services.embedding_service import EmbeddingService
from app.services.property_document_service import (
    PropertyDocumentService,
)


def test_property_embedding_repository_save_and_find():
    db = SessionLocal()

    try:
        property_ = (
            db.query(Property)
            .order_by(Property.id)
            .first()
        )

        assert property_ is not None

        document_service = PropertyDocumentService()
        embedding_service = EmbeddingService()

        content = document_service.build_document(
            property_
        )

        embedding = embedding_service.embed_document(
            content
        )

        assert len(embedding) == 384

        repository = PropertyEmbeddingRepository(db)

        existing = repository.find_by_property_id(
            property_.id
        )

        if existing is not None:
            db.delete(existing)
            db.commit()

        property_embedding = PropertyEmbedding(
            property_id=property_.id,
            content=content,
            embedding=embedding,
            embedding_model=EmbeddingService.MODEL_NAME,
        )

        saved = repository.save(
            property_embedding
        )

        found = repository.find_by_property_id(
            property_.id
        )

        assert saved.id is not None
        assert found is not None
        assert found.property_id == property_.id
        assert found.content == content
        assert (
                found.embedding_model
                == EmbeddingService.MODEL_NAME
        )
        assert len(found.embedding) == 384

    finally:
        if "property_" in locals() and property_ is not None:
            existing = (
                db.query(PropertyEmbedding)
                .filter(
                    PropertyEmbedding.property_id
                    == property_.id
                )
                .first()
            )

            if existing is not None:
                db.delete(existing)
                db.commit()

        db.close()