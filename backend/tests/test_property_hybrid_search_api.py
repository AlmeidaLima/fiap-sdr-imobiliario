from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.property import Property


client = TestClient(app)


def create_property() -> Property:
    property_ = Property(
        id=999999,
        external_id="hybrid-api-test-001",
        title="Apartamento com excelente área de lazer",
        description=(
            "Apartamento com academia, churrasqueira "
            "e salão de festas."
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
        street="Rua de Teste",
        neighborhood="Boa Vista",
        pois=[],
        price=600000,
        source="test",
        available=True,
    )

    return property_


@patch(
    "app.api.routes.properties."
    "PropertyHybridSearchService.search"
)
def test_hybrid_search_returns_results(
        mock_search,
):
    property_ = create_property()

    property_embedding = type(
        "PropertyEmbeddingMock",
        (),
        {
            "property": property_,
        },
    )()

    mock_search.return_value = [
        (
            property_embedding,
            0.9123,
        )
    ]

    response = client.get(
        "/api/v1/properties/hybrid-search",
        params={
            "q": "apartamento com boa área de lazer",
            "neighborhood": "Boa Vista",
            "max_price": 700000,
            "min_bedrooms": 3,
            "limit": 5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    result = body[0]

    assert result["id"] == 999999
    assert (
            result["external_id"]
            == "hybrid-api-test-001"
    )
    assert result["neighborhood"] == "Boa Vista"
    assert result["bedrooms"] == 3
    assert result["price"] == "600000"
    assert result["similarity_score"] == 0.9123


def test_hybrid_search_requires_query():
    response = client.get(
        "/api/v1/properties/hybrid-search"
    )

    assert response.status_code == 422


def test_hybrid_search_rejects_short_query():
    response = client.get(
        "/api/v1/properties/hybrid-search",
        params={
            "q": "ab",
        },
    )

    assert response.status_code == 422


def test_hybrid_search_rejects_invalid_limit():
    response = client.get(
        "/api/v1/properties/hybrid-search",
        params={
            "q": "apartamento",
            "limit": 21,
        },
    )

    assert response.status_code == 422


def test_hybrid_search_rejects_negative_price():
    response = client.get(
        "/api/v1/properties/hybrid-search",
        params={
            "q": "apartamento",
            "max_price": -1,
        },
    )

    assert response.status_code == 422