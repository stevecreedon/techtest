import pytest

from app.services.export_service import ExportService


def test_create_export_then_get_export_roundtrips_csv():
    service = ExportService()
    rows = [
        {"label": "0th-25th percentile", "count": 27},
        {"label": "25th-50th percentile", "count": 27},
    ]

    export_id = service.create_export(rows, filename="women_by_quartile.csv")
    export = service.get_export(export_id)

    assert export is not None
    assert export.filename == "women_by_quartile.csv"
    csv_text = export.csv_bytes.decode("utf-8")
    assert "label,count" in csv_text
    assert "0th-25th percentile,27" in csv_text


def test_get_export_returns_none_for_unknown_id():
    service = ExportService()

    assert service.get_export("does-not-exist") is None


def test_create_export_rejects_empty_rows():
    service = ExportService()

    with pytest.raises(ValueError):
        service.create_export([])
