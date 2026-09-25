from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_questions():
    response = client.get("/ask")

    assert response.status_code == 200


def test_chat():
    response = client.post(
        "/chat",
        json={
            "question": "What is 2 + 2?"
        }
    )

    assert response.status_code == 200