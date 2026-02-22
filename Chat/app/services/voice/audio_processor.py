"""
Audio Processor — File I/O helpers for voice pipeline.
Handles saving uploads, generating output paths, and format conversion.
"""

import os
import uuid
import logging

logger = logging.getLogger(__name__)

VOICE_UPLOAD_DIR = "storage/voice_uploads"
TTS_OUTPUT_DIR = "storage/tts_outputs"


def ensure_directories():
    os.makedirs(VOICE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def save_uploaded_audio(file_bytes: bytes, extension: str = "wav") -> str:
    """Save raw uploaded audio bytes to disk."""
    ensure_directories()
    filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(VOICE_UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    logger.info(f"Saved uploaded audio to {file_path} ({len(file_bytes)} bytes)")
    return file_path


def generate_tts_output_path(extension: str = "wav") -> str:
    """Generate a unique output path for TTS audio."""
    ensure_directories()
    filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join(TTS_OUTPUT_DIR, filename)


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio format (webm, ogg, mp3) to WAV 16kHz mono
    using pydub. Returns the path to the converted WAV file.
    """
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)

        wav_path = input_path.rsplit(".", 1)[0] + "_converted.wav"
        audio.export(wav_path, format="wav")

        logger.info(f"Converted {input_path} → {wav_path}")
        return wav_path
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e}. Using original file.")
        return input_path
