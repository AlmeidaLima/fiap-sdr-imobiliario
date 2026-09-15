from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_semantic_search_requires_query():
    response = client.get(
        "/api/v1/properties/semantic-search"
    )

    assert response.status_code == 422


def test_semantic_search_rejects_short_query():
    response = client.get(
        "/api/v1/properties/semantic-search",
        params={
            "q": "ab",
        },
    )

    assert response.status_code == 422


def test_semantic_search_returns_results():
    response = client.get(
        "/api/v1/properties/semantic-search",
        params={
            "q": "apartamento com academia e churrasqueira",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)
    assert len(body) <= 5

    if body:
        result = body[0]

        assert "id" in result
        assert "external_id" in result
        assert "title" in result
        assert "neighborhood" in result
        assert "similarity_score" in result

        assert 0.0 <= result["similarity_score"] <= 1.0


def test_semantic_search_respects_limit():
    response = client.get(
        "/api/v1/properties/semantic-search",
        params={
            "q": "apartamento com piscina e academia",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)
    assert len(body) <= 3


def test_semantic_search_rejects_invalid_limit():
    response = client.get(
        "/api/v1/properties/semantic-search",
        params={
            "q": "apartamento com academia",
            "limit": 21,
        },
    )

    assert response.status_code == 422