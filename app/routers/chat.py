from pathlib import Path

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates

from app.dependencies import get_chat_service
from app.schemas.chat import ChatMessageIn
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html")


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message_in = ChatMessageIn.model_validate(data)
            response = await chat_service.get_response(message_in.message)
            await websocket.send_json({"message": response})
    except WebSocketDisconnect:
        pass
