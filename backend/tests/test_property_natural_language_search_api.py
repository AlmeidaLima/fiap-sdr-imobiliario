from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.property import Property


client = TestClient(app)


def create_property() -> Property:
    return Property(
        id=999999,
        external_id="natural-language-api-test-001",
        title="Apartamento com academia e churrasqueira",
        description=(
            "Apartamento para família com excelente "
            "área de lazer."
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


@patch(
    "app.api.routes.properties."
    "PropertyNaturalLanguageSearchService.search"
)
def test_natural_language_search_returns_results(
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

    response = client.post(
        "/api/v1/properties/natural-language-search",
        json={
            "message": (
                "Quero apartamento no Boa Vista "
                "com 3 quartos, até 700 mil, "
                "academia e churrasqueira."
            ),
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
            == "natural-language-api-test-001"
    )
    assert result["neighborhood"] == "Boa Vista"
    assert result["bedrooms"] == 3
    assert result["usable_area"] == 90
    assert result["similarity_score"] == 0.9123


def test_natural_language_search_requires_message():
    response = client.post(
        "/api/v1/properties/natural-language-search",
        json={
            "limit": 5,
        },
    )

    assert response.status_code == 422


def test_natural_language_search_rejects_short_message():
    response = client.post(
        "/api/v1/properties/natural-language-search",
        json={
            "message": "ab",
            "limit": 5,
        },
    )

    assert response.status_code == 422


def test_natural_language_search_rejects_invalid_limit():
    response = client.post(
        "/api/v1/properties/natural-language-search",
        json={
            "message": "Quero um apartamento",
            "limit": 21,
        },
    )

    assert response.status_code == 422


def test_natural_language_search_uses_default_limit():
    with patch(
            "app.api.routes.properties."
            "PropertyNaturalLanguageSearchService.search"
    ) as mock_search:

        mock_search.return_value = []

        response = client.post(
            "/api/v1/properties/natural-language-search",
            json={
                "message": "Quero um apartamento",
            },
        )

        assert response.status_code == 200

        mock_search.assert_called_once()

        call_arguments = mock_search.call_args.kwargs

        assert call_arguments["limit"] == 5