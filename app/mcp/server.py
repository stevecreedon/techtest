from mcp.server.fastmcp import FastMCP

from app.schemas.people import AverageAgeResult, BucketCountsResult, PercentileAgeResult, PersonOut

# `get_people_service` is imported lazily inside each tool below (rather than
# at module scope) to avoid a circular import: app.dependencies builds
# ChatService, which needs this module's mcp_server, which would otherwise
# need app.dependencies at import time.

mcp_server = FastMCP(
    name="people-query",
    instructions=(
        "Query and aggregate a dataset of people by country, region, age and gender. "
        "SSN, name and address are never available through this tool — only "
        "country, age and gender. Combine filters into a single call rather than "
        "issuing several narrower ones, and prefer the aggregate tools "
        "(average_age, age_percentile, bucket_counts) over query when you only "
        "need a number, to keep responses small."
    ),
)


@mcp_server.tool()
def list_countries() -> list[str]:
    """Return the unique, sorted list of countries present in the dataset."""
    from app.dependencies import get_people_service

    return get_people_service().list_countries()


@mcp_server.tool()
def query_people(
    countries: list[str] | None = None,
    region: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
) -> list[PersonOut]:
    """Return matching people as {country, age, gender} — never name/ssn/address.

    Filter by an exact country, an array of countries, or a region (e.g.
    'South America'); optionally combine with an age range (age_min and/or
    age_max) and/or an exact gender match. All filters apply together in one
    call. Prefer average_age/age_percentile/bucket_counts when you only need
    a statistic, since this returns raw rows.
    """
    from app.dependencies import get_people_service

    return get_people_service().query(
        countries=countries,
        region=region,
        age_min=age_min,
        age_max=age_max,
        gender=gender,
    )


@mcp_server.tool()
def average_age(
    countries: list[str] | None = None,
    region: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
) -> AverageAgeResult:
    """Return the average age for people matching the given filters.

    E.g. average_age(region="South America", gender="male") answers
    "What is the average age of men in South America?".
    """
    from app.dependencies import get_people_service

    return get_people_service().average_age(
        countries=countries, region=region, age_min=age_min, age_max=age_max, gender=gender
    )


@mcp_server.tool()
def age_percentile(
    percentile: float,
    countries: list[str] | None = None,
    region: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
) -> PercentileAgeResult:
    """Return the age at a given percentile (0-100) for people matching the filters.

    E.g. age_percentile(90) answers "What age range is below the 90th
    percentile by age?" — the range is min_age to the returned
    age_at_percentile.
    """
    from app.dependencies import get_people_service

    return get_people_service().age_percentile(
        percentile,
        countries=countries,
        region=region,
        age_min=age_min,
        age_max=age_max,
        gender=gender,
    )


@mcp_server.tool()
def bucket_counts(
    percentile_edges: list[float],
    countries: list[str] | None = None,
    region: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
) -> BucketCountsResult:
    """Count people by age percentile bucket for people matching the filters.

    E.g. bucket_counts([25, 50, 75, 100], gender="female") answers "Aggregate
    the number of women by 25th, 25-50th, 50-75th and 75-100th percentile."
    """
    from app.dependencies import get_people_service

    return get_people_service().bucket_counts(
        percentile_edges,
        countries=countries,
        region=region,
        age_min=age_min,
        age_max=age_max,
        gender=gender,
    )
