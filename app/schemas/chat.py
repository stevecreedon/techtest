from typing import Literal

from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    message: str


class ChatEvent(BaseModel):
    """One increment of a streamed chat turn, sent over the websocket as JSON."""

    type: Literal["thinking", "tool_call", "tool_result", "answer", "download"]
    text: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    download_url: str | None = None
