import pytest

from app.config import settings
from app.repositories.region_repository import RegionRepository, UnknownRegionError


def test_countries_for_region_returns_expected_south_american_countries():
    repo = RegionRepository(settings.regions_path)

    countries = repo.countries_for_region("South America")

    assert "Brazil" in countries
    assert "Argentina" in countries
    assert "Japan" not in countries


def test_countries_for_region_is_case_insensitive():
    repo = RegionRepository(settings.regions_path)

    assert repo.countries_for_region("south america") == repo.countries_for_region("South America")


def test_unknown_region_raises_clear_error():
    repo = RegionRepository(settings.regions_path)

    with pytest.raises(UnknownRegionError):
        repo.countries_for_region("Narnia")
