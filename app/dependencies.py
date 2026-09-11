from functools import lru_cache

from app.config import settings
from app.repositories.people_repository import PeopleRepository
from app.repositories.region_repository import RegionRepository
from app.services.chat_service import ChatService
from app.services.export_service import ExportService
from app.services.llm_client import AnthropicLLMClient, FakeLLMClient, LLMClient
from app.services.people_service import PeopleService


@lru_cache
def get_people_repository() -> PeopleRepository:
    return PeopleRepository(settings.people_csv_path)


@lru_cache
def get_region_repository() -> RegionRepository:
    return RegionRepository(settings.regions_path)


def get_people_service() -> PeopleService:
    return PeopleService(get_people_repository(), get_region_repository())


@lru_cache
def get_export_service() -> ExportService:
    return ExportService()


@lru_cache
def get_llm_client() -> LLMClient:
    if settings.anthropic_api_key:
        return AnthropicLLMClient(
            api_key=settings.anthropic_api_key, model=settings.anthropic_model
        )
    return FakeLLMClient()


def get_chat_service() -> ChatService:
    return ChatService(get_llm_client(), get_export_service())
