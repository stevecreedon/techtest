import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PersonRecord:
    country: str
    age: int
    gender: str


class PeopleRepository:
    """Loads people data from a CSV file, discarding PII columns on ingestion.

    Only country/age/gender ever exist in memory past the parse of a single
    row — name/ssn/address are read and immediately dropped, so there is no
    code path anywhere downstream that could leak them.
    """

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path
        self._records: list[PersonRecord] | None = None

    def get_all(self) -> list[PersonRecord]:
        if self._records is None:
            self._records = list(self._load())
        return self._records

    def _load(self) -> Iterable[PersonRecord]:
        with self._csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield PersonRecord(
                    country=row["country"],
                    age=int(row["age"]),
                    gender=row["gender"],
                )
