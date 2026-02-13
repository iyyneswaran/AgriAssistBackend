from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from app.core.rate_limiter import rate_limit_dependency

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/upload", dependencies=[Depends(rate_limit_dependency)])
async def upload_voice(file: UploadFile = File(...)):
    content = await file.read()

    file_path = f"storage/voice_uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    return JSONResponse(
        {
            "status": "uploaded",
            "file_path": file_path
        }
    )
