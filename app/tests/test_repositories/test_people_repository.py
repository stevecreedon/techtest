from pathlib import Path

from app.repositories.people_repository import PeopleRepository

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "people_sample.csv"


def test_get_all_loads_every_row():
    repo = PeopleRepository(FIXTURE_PATH)

    records = repo.get_all()

    assert len(records) == 5


def test_records_never_expose_pii_fields():
    repo = PeopleRepository(FIXTURE_PATH)

    records = repo.get_all()

    for record in records:
        field_names = {f for f in record.__dataclass_fields__}
        assert field_names == {"country", "age", "gender"}


def test_get_all_caches_after_first_load():
    repo = PeopleRepository(FIXTURE_PATH)

    first = repo.get_all()
    second = repo.get_all()

    assert first is second
