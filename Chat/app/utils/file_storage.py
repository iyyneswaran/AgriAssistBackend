import os
import uuid
from typing import BinaryIO


BASE_STORAGE_PATH = "storage"


def ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)


def save_file(file_bytes: bytes, folder: str, extension: str) -> str:
    directory = os.path.join(BASE_STORAGE_PATH, folder)
    ensure_directory(directory)

    filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(directory, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_path


def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
