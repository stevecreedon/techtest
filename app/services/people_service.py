import math

from app.repositories.people_repository import PeopleRepository, PersonRecord
from app.repositories.region_repository import RegionRepository
from app.schemas.people import (
    AverageAgeResult,
    BucketCount,
    BucketCountsResult,
    PercentileAgeResult,
    PersonOut,
)


def _percentile(sorted_values: list[int], percentile: float) -> float:
    """Linear-interpolation percentile, matching numpy's default method."""
    if not sorted_values:
        raise ValueError("Cannot compute a percentile of an empty sample")
    if len(sorted_values) == 1:
        return float(sorted_values[0])

    rank = (len(sorted_values) - 1) * (percentile / 100)
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)
    if lower_index == upper_index:
        return float(sorted_values[int(rank)])

    lower_value = sorted_values[lower_index] * (upper_index - rank)
    upper_value = sorted_values[upper_index] * (rank - lower_index)
    return lower_value + upper_value


class PeopleService:
    """PII-safe filtering and aggregation over people data.

    Every method here operates on PersonRecord (country/age/gender only) and
    returns schemas that likewise carry no name/ssn/address fields.
    """

    def __init__(self, people_repo: PeopleRepository, region_repo: RegionRepository) -> None:
        self._people_repo = people_repo
        self._region_repo = region_repo

    def list_countries(self) -> list[str]:
        return sorted({record.country for record in self._people_repo.get_all()})

    def query(
        self,
        countries: list[str] | None = None,
        region: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        gender: str | None = None,
    ) -> list[PersonOut]:
        records = self._filter(countries, region, age_min, age_max, gender)
        return [PersonOut(country=r.country, age=r.age, gender=r.gender) for r in records]

    def average_age(
        self,
        countries: list[str] | None = None,
        region: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        gender: str | None = None,
    ) -> AverageAgeResult:
        ages = [r.age for r in self._filter(countries, region, age_min, age_max, gender)]
        if not ages:
            return AverageAgeResult(value=None, sample_size=0)
        return AverageAgeResult(value=sum(ages) / len(ages), sample_size=len(ages))

    def age_percentile(
        self,
        percentile: float,
        countries: list[str] | None = None,
        region: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        gender: str | None = None,
    ) -> PercentileAgeResult:
        ages = sorted(r.age for r in self._filter(countries, region, age_min, age_max, gender))
        if not ages:
            raise ValueError("No matching records to compute a percentile from")
        return PercentileAgeResult(
            percentile=percentile,
            age_at_percentile=_percentile(ages, percentile),
            min_age=ages[0],
            max_age=ages[-1],
            sample_size=len(ages),
        )

    def bucket_counts(
        self,
        percentile_edges: list[float],
        countries: list[str] | None = None,
        region: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        gender: str | None = None,
    ) -> BucketCountsResult:
        ages = sorted(r.age for r in self._filter(countries, region, age_min, age_max, gender))
        if not ages:
            raise ValueError("No matching records to bucket")

        edges = sorted(percentile_edges)
        boundaries = [(0.0, ages[0])] + [(edge, _percentile(ages, edge)) for edge in edges]

        buckets = []
        for (lower_pct, lower_val), (upper_pct, upper_val) in zip(boundaries, boundaries[1:]):
            is_first = lower_pct == 0.0
            count = sum(
                1
                for age in ages
                if (age >= lower_val if is_first else age > lower_val) and age <= upper_val
            )
            buckets.append(
                BucketCount(
                    label=f"{lower_pct:g}th-{upper_pct:g}th percentile",
                    lower_percentile=lower_pct,
                    upper_percentile=upper_pct,
                    count=count,
                )
            )

        return BucketCountsResult(field="age", buckets=buckets, sample_size=len(ages))

    def _filter(
        self,
        countries: list[str] | None,
        region: str | None,
        age_min: int | None,
        age_max: int | None,
        gender: str | None,
    ) -> list[PersonRecord]:
        allowed_countries: set[str] | None = None
        if countries:
            allowed_countries = {c.lower() for c in countries}
        if region:
            region_countries = {c.lower() for c in self._region_repo.countries_for_region(region)}
            allowed_countries = (
                region_countries
                if allowed_countries is None
                else allowed_countries & region_countries
            )

        records = self._people_repo.get_all()
        result = []
        for record in records:
            if allowed_countries is not None and record.country.lower() not in allowed_countries:
                continue
            if age_min is not None and record.age < age_min:
                continue
            if age_max is not None and record.age > age_max:
                continue
            if gender is not None and record.gender.lower() != gender.lower():
                continue
            result.append(record)
        return result
