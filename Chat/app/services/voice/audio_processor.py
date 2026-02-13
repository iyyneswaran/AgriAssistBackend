import os
import uuid


VOICE_UPLOAD_DIR = "storage/voice_uploads"
TTS_OUTPUT_DIR = "storage/tts_outputs"


def ensure_directories():
    os.makedirs(VOICE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def save_uploaded_audio(file_bytes: bytes, extension: str = "ogg") -> str:
    ensure_directories()
    filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(VOICE_UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_path


def generate_tts_output_path(extension: str = "ogg") -> str:
    ensure_directories()
    filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join(TTS_OUTPUT_DIR, filename)
