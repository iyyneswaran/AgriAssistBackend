"""
Voice API Router — Endpoints for STT, TTS, and the full voice pipeline.
"""

from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.responses import JSONResponse, FileResponse
from app.core.rate_limiter import rate_limit_dependency
from app.services.voice.stt_service import speech_to_text
from app.services.voice.tts_service import text_to_speech
from app.services.voice.audio_processor import save_uploaded_audio, convert_to_wav
from app.core.config import settings
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])

# Ensure upload directory exists
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "storage" / "voice_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", dependencies=[Depends(rate_limit_dependency)])
async def upload_voice(file: UploadFile = File(...)):
    """Upload a voice file (backward-compatible endpoint)."""
    content = await file.read()
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    return JSONResponse(
        {"status": "uploaded", "file_path": str(file_path)}
    )


@router.post("/transcribe", dependencies=[Depends(rate_limit_dependency)])
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = Form(default=None),
):
    """
    Speech-to-Text: Upload audio file → get transcribed text.
    Accepts any audio format (wav, webm, ogg, mp3).
    Returns: { text, language }
    """
    lang = language or settings.VOICE_LANGUAGE

    # Save uploaded file
    content = await file.read()
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "wav"
    audio_path = save_uploaded_audio(content, extension=ext)

    # Convert to WAV if not already (browser usually sends webm)
    if ext not in ("wav",):
        audio_path = convert_to_wav(audio_path)

    # Run STT
    try:
        result = await speech_to_text(audio_path, language=lang)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"STT error: {e}")
        return JSONResponse(
            {"error": str(e), "text": "", "language": lang},
            status_code=500,
        )


@router.post("/synthesize", dependencies=[Depends(rate_limit_dependency)])
async def synthesize_speech(
    text: str = Form(...),
    language: str = Form(default=None),
):
    """
    Text-to-Speech: Send text → get audio file back.
    Returns: audio file (WAV/FLAC) as a downloadable response.
    """
    lang = language or settings.VOICE_LANGUAGE

    try:
        audio_path = await text_to_speech(text=text, language=lang)

        if not os.path.exists(audio_path):
            return JSONResponse(
                {"error": "TTS output file not found"},
                status_code=500,
            )

        # Determine media type from extension
        ext = audio_path.rsplit(".", 1)[-1]
        media_types = {
            "wav": "audio/wav",
            "flac": "audio/flac",
            "ogg": "audio/ogg",
            "mp3": "audio/mpeg",
        }
        media_type = media_types.get(ext, "audio/wav")

        return FileResponse(
            path=audio_path,
            media_type=media_type,
            filename=f"tts_output.{ext}",
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )
