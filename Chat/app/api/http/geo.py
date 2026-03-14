from fastapi import APIRouter, HTTPException
from app.schemas.geo import GeoAnalyzeRequest, GeoAnalyzeResponse
import logging

router = APIRouter(prefix="/geo", tags=["Geo Analysis"])

logger = logging.getLogger(__name__)
geo_service = None


def get_geo_service():
    global geo_service
    if geo_service is None:
        from app.services.geo.geo_analysis_service import GeoAnalysisService
        geo_service = GeoAnalysisService()
    return geo_service


@router.post("/analyze", response_model=GeoAnalyzeResponse)
async def analyze_geo(payload: GeoAnalyzeRequest):
    """
    Analyze farm geospatial data using Google Earth Engine.
    """

    try:
        if payload.latitude is None or payload.longitude is None:
            raise HTTPException(status_code=400, detail="Latitude and longitude required")

        service = get_geo_service()
        result = service.analyze(payload.latitude, payload.longitude)

        return result

    except ModuleNotFoundError as e:
        logger.error(f"Geo dependency missing: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Geo feature dependency missing: {str(e)}"
        )
    except (EnvironmentError, RuntimeError) as e:
        logger.error(f"Geo service unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Geo service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geo analysis failed: {str(e)}"
        )
