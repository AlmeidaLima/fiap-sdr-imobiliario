from decimal import Decimal

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.property import Property


client = TestClient(app)

TEST_NEIGHBORHOOD = "__TEST_PROPERTIES_API__"

TEST_EXTERNAL_IDS = [
    "test-api-property-001",
    "test-api-property-002",
    "test-api-property-003",
]


def cleanup_test_properties(db) -> None:
    """
    Remove registros utilizados pelos testes da API.

    A limpeza é executada antes e depois do teste para garantir
    que resíduos de execuções anteriores não provoquem conflito
    com a constraint UNIQUE de external_id.
    """

    db.query(Property).filter(
        Property.external_id.in_(TEST_EXTERNAL_IDS)
    ).delete(
        synchronize_session=False
    )

    db.commit()


def test_properties_returns_empty_list_when_no_match():
    response = client.get(
        "/api/v1/properties",
        params={
            "neighborhood": "__BAIRRO_INEXISTENTE_TESTE__",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body == []


def test_properties_returns_filtered_results():
    db = SessionLocal()

    try:
        # Remove possíveis resíduos de execuções anteriores.
        cleanup_test_properties(db)

        property_1 = Property(
            external_id="test-api-property-001",
            title="Apartamento Centro 1",
            description="Imóvel de teste",
            usable_area=80,
            bathrooms=2,
            bedrooms=3,
            parking_spaces=2,
            amenities=["academia"],
            zip_code="80000001",
            street="Rua A",
            neighborhood=TEST_NEIGHBORHOOD,
            pois=[],
            price=Decimal("550000.00"),
            source="test",
            available=True,
        )

        property_2 = Property(
            external_id="test-api-property-002",
            title="Apartamento Centro 2",
            description="Imóvel de teste",
            usable_area=60,
            bathrooms=1,
            bedrooms=2,
            parking_spaces=1,
            amenities=[],
            zip_code="80000002",
            street="Rua B",
            neighborhood=TEST_NEIGHBORHOOD,
            pois=[],
            price=Decimal("450000.00"),
            source="test",
            available=True,
        )

        property_3 = Property(
            external_id="test-api-property-003",
            title="Apartamento Outro Bairro",
            description="Imóvel de teste",
            usable_area=90,
            bathrooms=2,
            bedrooms=3,
            parking_spaces=2,
            amenities=[],
            zip_code="80000003",
            street="Rua C",
            neighborhood="Batel",
            pois=[],
            price=Decimal("500000.00"),
            source="test",
            available=True,
        )

        db.add_all(
            [
                property_1,
                property_2,
                property_3,
            ]
        )

        db.commit()

        response = client.get(
            "/api/v1/properties",
            params={
                "neighborhood": TEST_NEIGHBORHOOD,
                "max_price": "500000",
                "min_bedrooms": 2,
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert len(body) == 1

        assert body[0]["title"] == "Apartamento Centro 2"
        assert body[0]["neighborhood"] == TEST_NEIGHBORHOOD
        assert body[0]["price"] == "450000.00"

    finally:
        # Caso algum comando anterior deixe a sessão em erro,
        # restaura a transação antes de executar a limpeza.
        db.rollback()

        cleanup_test_properties(db)

        db.close()