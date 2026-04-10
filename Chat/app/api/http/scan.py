"""
Scan Crop Router — Disease detection and remedy generation endpoints.
Handles image upload, validation, ML inference, and AI remedy generation.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.schemas.scan_schemas import (
    ScanPredictResponse,
    RemedyRequest,
    RemedyResponse,
    ScanAnalyzeResponse,
    SensorContext,
)
from app.services.scan.model_service import predict
from app.services.scan.remedy_service import generate_remedy
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["Scan Crop"])

# ── Constants ──
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


def _validate_upload(file: UploadFile) -> None:
    """Validate uploaded file: MIME type and size."""
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only JPEG and PNG images are accepted.",
        )

    # Check filename extension as secondary validation
    if file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ("jpg", "jpeg", "png"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file extension. Only .jpg, .jpeg, and .png are accepted.",
            )


async def _read_and_validate_bytes(file: UploadFile) -> bytes:
    """Read file bytes with size validation."""
    contents = await file.read()

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)}MB.",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # Validate magic bytes (JPEG: FF D8 FF, PNG: 89 50 4E 47)
    if contents[:3] == b"\xff\xd8\xff":
        pass  # Valid JPEG
    elif contents[:4] == b"\x89PNG":
        pass  # Valid PNG
    else:
        raise HTTPException(
            status_code=400,
            detail="File content does not match a valid JPEG or PNG image.",
        )

    return contents


# ─────────────────────────────────────────────
# POST /api/scan/predict — Image → Disease Prediction
# ─────────────────────────────────────────────
@router.post("/predict", response_model=ScanPredictResponse)
async def predict_disease(file: UploadFile = File(...)):
    """
    Upload a crop leaf image (JPEG/PNG, ≤10MB) for disease detection.
    Returns: disease name, crop name, and confidence score.
    """
    _validate_upload(file)
    image_bytes = await _read_and_validate_bytes(file)

    try:
        result = predict(image_bytes)
        return ScanPredictResponse(**result)
    except RuntimeError as e:
        logger.error(f"[Scan] Model inference error: {e}")
        raise HTTPException(status_code=503, detail="Disease detection model is not available.")
    except Exception as e:
        logger.error(f"[Scan] Prediction error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze the image. Please try again.")


# ─────────────────────────────────────────────
# POST /api/scan/remedy — Disease → AI Remedy
# ─────────────────────────────────────────────
@router.post("/remedy", response_model=RemedyResponse)
async def get_remedy(request: RemedyRequest):
    """
    Generate an AI-powered remedy for a detected disease.
    Optionally includes IoT sensor data for personalized advice.
    """
    try:
        result = await generate_remedy(
            disease_label=request.disease_label,
            crop_type=request.crop_type,
            sensor_data=request.sensor_data,
        )
        return RemedyResponse(**result)
    except Exception as e:
        logger.error(f"[Scan] Remedy generation error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate remedy. Please try again.")


# ─────────────────────────────────────────────
# POST /api/scan/analyze — Image → Prediction + Remedy (combo)
# ─────────────────────────────────────────────
@router.post("/analyze", response_model=ScanAnalyzeResponse)
async def analyze_crop(
    file: UploadFile = File(...),
    sensor_data: str = Form(default=""),
):
    """
    Combined endpoint: uploads an image, runs disease detection,
    then generates an AI remedy with live IoT sensor data.
    """
    # 1. Validate and read image
    _validate_upload(file)
    image_bytes = await _read_and_validate_bytes(file)

    # 2. Parse optional sensor data JSON
    sensor_ctx = None
    if sensor_data and sensor_data.strip():
        try:
            sensor_dict = json.loads(sensor_data)
            sensor_ctx = SensorContext(**sensor_dict)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[Scan] Invalid sensor_data JSON, ignoring: {e}")

    # 3. Run prediction
    try:
        prediction_result = predict(image_bytes)
    except RuntimeError as e:
        logger.error(f"[Scan] Model inference error: {e}")
        raise HTTPException(status_code=503, detail="Disease detection model is not available.")
    except Exception as e:
        logger.error(f"[Scan] Prediction error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze the image. Please try again.")

    # 4. Generate remedy
    try:
        remedy_result = await generate_remedy(
            disease_label=prediction_result["disease_label"],
            crop_type=prediction_result["crop_name"],
            sensor_data=sensor_ctx,
        )
    except Exception as e:
        logger.error(f"[Scan] Remedy error: {type(e).__name__}: {e}")
        # Return prediction even if remedy fails
        from app.services.scan.fallback_remedies import get_fallback_remedy
        remedy_result = get_fallback_remedy(prediction_result["disease_label"])

    return ScanAnalyzeResponse(
        prediction=ScanPredictResponse(**prediction_result),
        remedy=RemedyResponse(**remedy_result),
    )
