from decimal import Decimal

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


TEST_EXTERNAL_IDS = [
    "hybrid-test-001",
    "hybrid-test-002",
    "hybrid-test-003",
]


def cleanup(db):
    properties = (
        db.query(Property)
        .filter(
            Property.external_id.in_(
                TEST_EXTERNAL_IDS
            )
        )
        .all()
    )

    for property_ in properties:
        db.delete(property_)

    db.commit()


def test_hybrid_search_applies_structured_filters():
    db = SessionLocal()

    try:
        cleanup(db)

        properties = [
            Property(
                external_id="hybrid-test-001",
                title=(
                    "Apartamento com academia "
                    "e churrasqueira"
                ),
                description=(
                    "Apartamento para família "
                    "com excelente área de lazer."
                ),
                usable_area=90,
                bathrooms=2,
                bedrooms=3,
                parking_spaces=2,
                amenities=[
                    "GYM",
                    "BARBECUE_GRILL",
                ],
                zip_code="80000001",
                street="Rua A",
                neighborhood="Bairro Teste Hibrido",
                pois=[],
                price=Decimal("600000.00"),
                source="test",
                available=True,
            ),
            Property(
                external_id="hybrid-test-002",
                title=(
                    "Apartamento com academia "
                    "e churrasqueira"
                ),
                description=(
                    "Apartamento para família "
                    "com excelente área de lazer."
                ),
                usable_area=90,
                bathrooms=2,
                bedrooms=3,
                parking_spaces=2,
                amenities=[
                    "GYM",
                    "BARBECUE_GRILL",
                ],
                zip_code="80000002",
                street="Rua B",
                neighborhood="Centro",
                pois=[],
                price=Decimal("600000.00"),
                source="test",
                available=True,
            ),
            Property(
                external_id="hybrid-test-003",
                title=(
                    "Apartamento com academia "
                    "e churrasqueira"
                ),
                description=(
                    "Apartamento para família "
                    "com excelente área de lazer."
                ),
                usable_area=90,
                bathrooms=2,
                bedrooms=3,
                parking_spaces=2,
                amenities=[
                    "GYM",
                    "BARBECUE_GRILL",
                ],
                zip_code="80000003",
                street="Rua C",
                neighborhood="Bairro Teste Hibrido",
                pois=[],
                price=Decimal("900000.00"),
                source="test",
                available=True,
            ),
        ]

        db.add_all(properties)
        db.commit()

        for property_ in properties:
            db.refresh(property_)

        document_service = PropertyDocumentService()
        embedding_service = EmbeddingService()
        repository = PropertyEmbeddingRepository(db)

        for property_ in properties:
            content = document_service.build_document(
                property_
            )

            embedding = embedding_service.embed_document(
                content
            )

            repository.save(
                PropertyEmbedding(
                    property_id=property_.id,
                    content=content,
                    embedding=embedding,
                    embedding_model=(
                        EmbeddingService.MODEL_NAME
                    ),
                )
            )

        query_embedding = (
            embedding_service.embed_query(
                "apartamento com academia "
                "e churrasqueira"
            )
        )

        results = (
            repository.search_similar_with_filters(
                query_embedding=query_embedding,
                neighborhood="Bairro Teste Hibrido",
                max_price=Decimal("700000.00"),
                min_bedrooms=3,
                limit=5,
            )
        )

        assert len(results) == 1

        property_embedding, similarity_score = (
            results[0]
        )

        assert (
                property_embedding.property.external_id
                == "hybrid-test-001"
        )

        assert (
            property_embedding.property.neighborhood
            == "Bairro Teste Hibrido"
        )

        assert (
                property_embedding.property.price
                <= Decimal("700000.00")
        )

        assert (
                property_embedding.property.bedrooms
                >= 3
        )

        assert 0.0 <= similarity_score <= 1.0

    finally:
        db.rollback()
        cleanup(db)
        db.close()