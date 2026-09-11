import json
from pathlib import Path


class UnknownRegionError(ValueError):
    def __init__(self, region: str) -> None:
        super().__init__(f"Unknown region: {region!r}")
        self.region = region


class RegionRepository:
    """Looks up which countries belong to a named region (e.g. 'South America')."""

    def __init__(self, regions_path: Path) -> None:
        self._regions_path = regions_path
        self._regions: dict[str, list[str]] | None = None

    def _load(self) -> dict[str, list[str]]:
        if self._regions is None:
            self._regions = json.loads(self._regions_path.read_text())
        return self._regions

    def list_regions(self) -> list[str]:
        return sorted(self._load().keys())

    def countries_for_region(self, region: str) -> list[str]:
        for name, countries in self._load().items():
            if name.lower() == region.lower():
                return countries
        raise UnknownRegionError(region)
