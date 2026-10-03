from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_versioning_prefix(client: TestClient) -> None:
    # Non-versioned path should 404
    response = client.get("/api/health")
    assert response.status_code == 404
