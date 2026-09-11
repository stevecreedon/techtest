from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest

import app.dependencies as dependencies_module
from app.repositories.people_repository import PeopleRepository
from app.repositories.region_repository import RegionRepository
from app.schemas.chat import ChatEvent
from app.services.chat_service import ChatService
from app.services.export_service import ExportService
from app.services.llm_client import FakeLLMClient
from app.services.people_service import PeopleService

FIXTURE_CSV = Path(__file__).resolve().parent.parent / "fixtures" / "people_sample.csv"
REGIONS_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "regions.json"


@pytest.fixture(autouse=True)
def fixture_backed_service(monkeypatch):
    service = PeopleService(PeopleRepository(FIXTURE_CSV), RegionRepository(REGIONS_JSON))
    monkeypatch.setattr(dependencies_module, "get_people_service", lambda: service)


@pytest.fixture
def chat_service() -> ChatService:
    return ChatService(FakeLLMClient(), ExportService())


def _collector() -> tuple[list[ChatEvent], Callable[[ChatEvent], Awaitable[None]]]:
    events: list[ChatEvent] = []

    async def emit(event: ChatEvent) -> None:
        events.append(event)

    return events, emit


async def test_handle_message_streams_thinking_then_answer(chat_service):
    events, emit = _collector()

    await chat_service.handle_message("Hello RWS", emit)

    types = [e.type for e in events]
    assert "thinking" in types
    assert types[-1] == "answer"


async def test_handle_message_average_age_of_men_in_south_america(chat_service):
    events, emit = _collector()

    await chat_service.handle_message("What is the average age of men in South America", emit)

    answer = next(e for e in events if e.type == "answer")
    assert "35.0" in answer.text  # John Roe (45, Argentina) + Carlos Diaz (25, Chile)


async def test_handle_message_never_leaks_pii(chat_service):
    events, emit = _collector()

    await chat_service.handle_message("Hello RWS", emit)

    for event in events:
        text = (event.text or "") + str(event.tool_input or "")
        for pii in ("Jane Doe", "123-45-6789", "1 Test St"):
            assert pii not in text
