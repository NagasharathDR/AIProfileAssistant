from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_profile_endpoint_returns_labelled_sample_data():
    response = client.get("/api/profile")

    assert response.status_code == 200
    profile = response.json()
    assert profile["profile_type"] == "sample"
    assert "not a real person's profile" in profile["notice"]
    assert profile["name"] == "Sample User"