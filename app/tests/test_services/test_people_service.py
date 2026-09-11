from pathlib import Path

import pytest

from app.repositories.people_repository import PeopleRepository
from app.repositories.region_repository import RegionRepository
from app.services.people_service import PeopleService

FIXTURE_CSV = Path(__file__).resolve().parent.parent / "fixtures" / "people_sample.csv"
REGIONS_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "regions.json"


@pytest.fixture
def service() -> PeopleService:
    return PeopleService(PeopleRepository(FIXTURE_CSV), RegionRepository(REGIONS_JSON))


def test_list_countries_returns_unique_sorted_countries(service):
    assert service.list_countries() == ["Argentina", "Brazil", "Chile", "China"]


def test_query_filters_by_country_and_gender(service):
    results = service.query(countries=["Brazil"], gender="female")

    assert {r.country for r in results} == {"Brazil"}
    assert all(r.gender == "female" for r in results)
    assert len(results) == 2


def test_query_results_never_contain_pii_fields(service):
    results = service.query()

    for person in results:
        assert set(person.model_dump().keys()) == {"country", "age", "gender"}


def test_average_age_of_men_in_south_america(service):
    result = service.average_age(region="South America", gender="male")

    assert result.sample_size == 2  # John Roe (Argentina, 45), Carlos Diaz (Chile, 25)
    assert result.value == pytest.approx(35.0)


def test_average_age_with_no_matches_returns_none(service):
    result = service.average_age(countries=["Wakanda"])

    assert result.value is None
    assert result.sample_size == 0


def test_age_percentile_90th(service):
    result = service.age_percentile(90)

    assert result.sample_size == 5
    assert result.min_age == 25
    assert result.max_age == 60
    assert result.age_at_percentile == pytest.approx(56.0)


def test_bucket_counts_for_women_by_quartile(service):
    result = service.bucket_counts([25, 50, 75, 100], gender="female")

    assert result.sample_size == 3
    assert sum(bucket.count for bucket in result.buckets) == 3
    assert len(result.buckets) == 4
