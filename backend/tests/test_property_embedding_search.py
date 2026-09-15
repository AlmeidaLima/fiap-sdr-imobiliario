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
    "semantic-test-001",
    "semantic-test-002",
    "semantic-test-003",
]


def cleanup(db):
    properties = (
        db.query(Property)
        .filter(
            Property.external_id.in_(TEST_EXTERNAL_IDS)
        )
        .all()
    )

    for property_ in properties:
        db.delete(property_)

    db.commit()


def test_semantic_search_returns_most_relevant_property():
    db = SessionLocal()

    try:
        cleanup(db)

        properties = [
            Property(
                external_id="semantic-test-001",
                title="Apartamento com academia e churrasqueira",
                description=(
                    "Apartamento ideal para família, "
                    "com academia, churrasqueira e salão de festas."
                ),
                usable_area=90,
                bathrooms=2,
                bedrooms=3,
                parking_spaces=2,
                amenities=[
                    "GYM",
                    "BARBECUE_GRILL",
                    "PARTY_HALL",
                ],
                zip_code="80000001",
                street="Rua A",
                neighborhood="Boa Vista",
                pois=[],
                price=600000,
                source="test",
                available=True,
            ),
            Property(
                external_id="semantic-test-002",
                title="Apartamento compacto no centro",
                description=(
                    "Apartamento pequeno próximo a comércio."
                ),
                usable_area=40,
                bathrooms=1,
                bedrooms=1,
                parking_spaces=0,
                amenities=[],
                zip_code="80000002",
                street="Rua B",
                neighborhood="Centro",
                pois=[],
                price=300000,
                source="test",
                available=True,
            ),
            Property(
                external_id="semantic-test-003",
                title="Apartamento próximo de transporte",
                description=(
                    "Apartamento próximo a terminal "
                    "e pontos de ônibus."
                ),
                usable_area=70,
                bathrooms=2,
                bedrooms=2,
                parking_spaces=1,
                amenities=[],
                zip_code="80000003",
                street="Rua C",
                neighborhood="Portão",
                pois=[
                    "BS:Ponto de ônibus",
                    "TS:Terminal",
                ],
                price=450000,
                source="test",
                available=True,
            ),
        ]

        db.add_all(properties)
        db.commit()

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
                    embedding_model=EmbeddingService.MODEL_NAME,
                )
            )

        query_embedding = embedding_service.embed_query(
            "apartamento para família com academia e churrasqueira"
        )

        results = repository.search_similar(
            query_embedding=query_embedding,
            limit=3,
        )

        assert len(results) == 3

        property_embedding, similarity_score = results[0]

        assert (
                property_embedding.property.external_id
                == "semantic-test-001"
        )

        assert 0.0 <= similarity_score <= 1.0

    finally:
        db.rollback()
        cleanup(db)
        db.close()