from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.identity import Principal, get_current_principal
from app.modules.well_log import (
    DEMO_LOG,
    WellLogAnalysisRequest,
    WellLogAnalysisResponse,
    WellLogFileAnalysisResponse,
    WellLogPoint,
    analyze_well_log,
    parse_well_log_file,
)

router = APIRouter(prefix="/well-log", tags=["well-log"])


@router.get("/demo", response_model=list[WellLogPoint])
def get_demo_log() -> list[WellLogPoint]:
    return DEMO_LOG


@router.post("/analyze", response_model=WellLogAnalysisResponse)
def analyze_log(request: WellLogAnalysisRequest) -> WellLogAnalysisResponse:
    return analyze_well_log(request)


@router.post("/analyze-file", response_model=WellLogFileAnalysisResponse)
async def analyze_uploaded_log(
    file: UploadFile = File(...),
    principal: Principal = Depends(get_current_principal),
) -> WellLogFileAnalysisResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File name is required")
    content = await file.read()
    if len(content) > get_settings().upload_max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds upload size limit")
    try:
        points = parse_well_log_file(file.filename, content)
        request = WellLogAnalysisRequest(points=points)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return WellLogFileAnalysisResponse(points=points, analysis=analyze_well_log(request))
