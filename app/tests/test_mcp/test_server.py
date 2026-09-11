import json
from pathlib import Path

import pytest

import app.dependencies as dependencies_module
from app.mcp.server import mcp_server
from app.repositories.people_repository import PeopleRepository
from app.repositories.region_repository import RegionRepository
from app.services.people_service import PeopleService

FIXTURE_CSV = Path(__file__).resolve().parent.parent / "fixtures" / "people_sample.csv"
REGIONS_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "regions.json"


@pytest.fixture(autouse=True)
def fixture_backed_service(monkeypatch):
    service = PeopleService(PeopleRepository(FIXTURE_CSV), RegionRepository(REGIONS_JSON))
    monkeypatch.setattr(dependencies_module, "get_people_service", lambda: service)


async def test_list_tools_exposes_all_five_tools():
    tools = await mcp_server.list_tools()

    assert {t.name for t in tools} == {
        "list_countries",
        "query_people",
        "average_age",
        "age_percentile",
        "bucket_counts",
    }


async def test_list_tools_schema_never_mentions_pii_fields():
    tools = await mcp_server.list_tools()

    for tool in tools:
        schema_text = json.dumps(tool.inputSchema) + json.dumps(tool.outputSchema or {})
        for pii_field in ("ssn", "address", '"name"'):
            assert pii_field not in schema_text.lower()


async def test_query_people_combines_filters_in_one_call():
    _content, structured = await mcp_server.call_tool(
        "query_people", {"region": "South America", "gender": "male"}
    )

    people = structured["result"]
    assert {p["country"] for p in people} == {"Argentina", "Chile"}
    assert all(p["gender"] == "male" for p in people)
    assert all(set(p.keys()) == {"country", "age", "gender"} for p in people)


async def test_average_age_of_men_in_south_america():
    _content, structured = await mcp_server.call_tool(
        "average_age", {"region": "South America", "gender": "male"}
    )

    assert structured["value"] == pytest.approx(35.0)
    assert structured["sample_size"] == 2


async def test_query_people_response_never_contains_pii():
    _content, structured = await mcp_server.call_tool("query_people", {})

    raw = json.dumps(structured)
    for pii_value in ("Jane Doe", "123-45-6789", "1 Test St"):
        assert pii_value not in raw
