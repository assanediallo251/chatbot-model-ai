from fastapi.testclient import TestClient

from app.main import create_app


def test_openapi_schema_is_available() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "ISI Chatbot API"
