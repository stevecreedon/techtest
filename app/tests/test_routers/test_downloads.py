from app.dependencies import get_export_service


async def test_download_export_returns_csv_attachment(client):
    export_service = get_export_service()
    export_id = export_service.create_export(
        [{"country": "Brazil", "age": 30, "gender": "female"}], filename="people.csv"
    )

    response = await client.get(f"/downloads/{export_id}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="people.csv"' in response.headers["content-disposition"]
    assert "Brazil" in response.text


async def test_download_export_404s_for_unknown_id(client):
    response = await client.get("/downloads/does-not-exist")

    assert response.status_code == 404
