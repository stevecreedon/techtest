import csv
import io
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Export:
    filename: str
    csv_bytes: bytes


class ExportService:
    """Turns tabular query/aggregate results into downloadable CSV files.

    Exports are held in memory only, keyed by a generated id — callers never
    pass PII in; rows come from PeopleService's PII-free schemas.
    """

    def __init__(self) -> None:
        self._exports: dict[str, Export] = {}

    def create_export(self, rows: list[dict], filename: str = "export.csv") -> str:
        if not rows:
            raise ValueError("Cannot export an empty result set")

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

        export_id = uuid.uuid4().hex
        csv_bytes = buffer.getvalue().encode("utf-8")
        self._exports[export_id] = Export(filename=filename, csv_bytes=csv_bytes)
        return export_id

    def get_export(self, export_id: str) -> Export | None:
        return self._exports.get(export_id)
