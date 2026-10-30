"""
Voice API Router — Endpoints for STT, TTS, and the full voice pipeline.
"""

from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from starlette.background import BackgroundTask
from app.core.rate_limiter import rate_limit_dependency
from app.services.voice.stt_service import speech_to_text
from app.services.voice.tts_service import text_to_speech
from app.services.voice.audio_processor import save_uploaded_audio, convert_to_wav, MAX_AUDIO_BYTES, ALLOWED_AUDIO_EXTENSIONS
from app.core.config import settings
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])

# Ensure upload directory exists
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "storage" / "voice_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def _save_upload(file: UploadFile) -> str:
    extension = Path(file.filename or 'audio.wav').suffix.lstrip('.').lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail='Unsupported audio format')
    content = await file.read(MAX_AUDIO_BYTES + 1)
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail='Audio exceeds 10 MB')
    if not content:
        raise HTTPException(status_code=400, detail='Audio is empty')
    return save_uploaded_audio(content, extension=extension)


@router.post("/upload", dependencies=[Depends(rate_limit_dependency)])
async def upload_voice(file: UploadFile = File(...)):
    """Upload a voice file (backward-compatible endpoint)."""
    file_path = await _save_upload(file)

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
    audio_path = await _save_upload(file)
    ext = Path(audio_path).suffix.lstrip('.')
    original_path = audio_path

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
            {"error": "Transcription failed", "text": "", "language": lang},
            status_code=500,
        )


    finally:
        for path in {original_path, audio_path}:
            if os.path.isfile(path):
                os.remove(path)


@router.post("/synthesize", dependencies=[Depends(rate_limit_dependency)])
async def synthesize_speech(
    text: str = Form(..., min_length=1, max_length=5000),
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
            background=BackgroundTask(os.remove, audio_path),
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return JSONResponse(
            {"error": "Speech synthesis failed"},
            status_code=500,
        )
