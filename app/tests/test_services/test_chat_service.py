from app.services.chat_service import ChatService


async def test_get_response_returns_hi_there():
    service = ChatService()

    response = await service.get_response("Hello RWS")

    assert response == "Hi there"
