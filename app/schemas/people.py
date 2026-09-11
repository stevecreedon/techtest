from pydantic import BaseModel


class PersonOut(BaseModel):
    """PII-free view of a person: country, age and gender only."""

    country: str
    age: int
    gender: str


class QueryFilters(BaseModel):
    countries: list[str] | None = None
    region: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    gender: str | None = None


class AverageAgeResult(BaseModel):
    metric: str = "average_age"
    value: float | None
    sample_size: int


class PercentileAgeResult(BaseModel):
    percentile: float
    age_at_percentile: float
    min_age: int
    max_age: int
    sample_size: int


class BucketCount(BaseModel):
    label: str
    lower_percentile: float
    upper_percentile: float
    count: int


class BucketCountsResult(BaseModel):
    field: str
    buckets: list[BucketCount]
    sample_size: int
