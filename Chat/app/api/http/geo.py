from fastapi import APIRouter, HTTPException
from app.services.geo.geo_analysis_service import GeoAnalysisService
from app.schemas.geo import GeoAnalyzeRequest, GeoAnalyzeResponse

router = APIRouter(prefix="/geo", tags=["Geo Analysis"])

geo_service = GeoAnalysisService()


@router.post("/analyze", response_model=GeoAnalyzeResponse)
async def analyze_geo(payload: GeoAnalyzeRequest):
    """
    Analyze farm geospatial data using Google Earth Engine.
    """

    try:
        if payload.latitude is None or payload.longitude is None:
            raise HTTPException(status_code=400, detail="Latitude and longitude required")

        result = geo_service.analyze(payload.latitude, payload.longitude)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geo analysis failed: {str(e)}"
        )