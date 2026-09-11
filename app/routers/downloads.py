from fastapi import APIRouter, Depends, HTTPException, Response

from app.dependencies import get_export_service
from app.services.export_service import ExportService

router = APIRouter(tags=["downloads"])


@router.get("/downloads/{export_id}")
async def download_export(
    export_id: str,
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    export = export_service.get_export(export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="Export not found")

    return Response(
        content=export.csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )
