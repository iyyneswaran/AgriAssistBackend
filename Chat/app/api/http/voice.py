from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from app.core.rate_limiter import rate_limit_dependency
from pathlib import Path
import os

router = APIRouter(prefix="/voice", tags=["Voice"])

# Ensure upload directory exists
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "storage" / "voice_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", dependencies=[Depends(rate_limit_dependency)])
async def upload_voice(file: UploadFile = File(...)):
    content = await file.read()

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    return JSONResponse(
        {
            "status": "uploaded",
            "file_path": str(file_path)
        }
    )

