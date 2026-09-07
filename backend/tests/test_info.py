from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_info_returns_application_information():
    response = client.get("/api/v1/info")

    assert response.status_code == 200
    assert response.json() == {
        "name": settings.app_name,
        "version": settings.app_version,
    }