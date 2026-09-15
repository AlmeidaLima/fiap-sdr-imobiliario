from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_status_ok():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["service"] == "agente-sdr-imobiliario-api"


def test_health_response_schema():
    response = client.get("/api/v1/health")

    body = response.json()

    assert "status" in body
    assert "service" in body

    assert isinstance(body["status"], str)
    assert isinstance(body["service"], str)