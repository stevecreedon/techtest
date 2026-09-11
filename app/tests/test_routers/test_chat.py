from fastapi.testclient import TestClient

from app.main import app


async def test_get_chat_page_returns_chat_ui(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'data-controller="chat"' in response.text
    assert "bg-gray-100" in response.text


def test_websocket_chat_replies_hi_there():
    with TestClient(app).websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "Hello RWS"})
        data = websocket.receive_json()

    assert data == {"message": "Hi there"}
