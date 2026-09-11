from fastapi.testclient import TestClient

from app.main import app


async def test_get_chat_page_returns_chat_ui(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'data-controller="chat"' in response.text
    assert "bg-gray-100" in response.text


def _collect_events_until(websocket, event_type: str, limit: int = 20) -> list[dict]:
    events = []
    for _ in range(limit):
        event = websocket.receive_json()
        events.append(event)
        if event["type"] == event_type:
            return events
    raise AssertionError(f"Never received a {event_type!r} event; got {events}")


def test_websocket_streams_thinking_before_the_final_answer():
    with TestClient(app).websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "Hello RWS"})
        events = _collect_events_until(websocket, "answer")

    types = [e["type"] for e in events]
    assert "thinking" in types
    assert types[-1] == "answer"
    assert events[-1]["text"]


def test_websocket_answers_average_age_of_men_in_south_america():
    with TestClient(app).websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "What is the average age of men in South America"})
        events = _collect_events_until(websocket, "answer")

    tool_calls = [e for e in events if e["type"] == "tool_call"]
    assert any(e["tool_name"] == "average_age" for e in tool_calls)

    answer = events[-1]["text"]
    assert "average age" in answer.lower()

    for pii in ("ssn", "address"):
        assert pii not in answer.lower()


def test_websocket_offers_download_for_tabular_quartile_result():
    message = "Aggregate the number of women by 25th, 25-50th, 50-75th and 75-100th percentile"
    with TestClient(app).websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": message})
        events = _collect_events_until(websocket, "download")

    download_event = events[-1]
    assert download_event["download_url"].startswith("/downloads/")
