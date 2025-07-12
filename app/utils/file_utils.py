import os
import shutil
import uuid
from datetime import datetime

from fastapi import UploadFile

ALLOWED_EXTENSIONS = {".stl", ".3mf"}
MAX_UPLOAD_SIZE_MB = 100


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[-1].lower()


def is_valid_model_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    ext = get_file_extension(original_filename)
    uid = uuid.uuid4().hex
    return f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{uid}{ext}"


def get_storage_paths(upload_dir: str, filename: str) -> tuple[str, str]:
    """
    Returns: (temp_path, final_path)
    """
    tmp_path = os.path.join(upload_dir, "tmp", filename)
    final_path = os.path.join(upload_dir, "models", filename)
    return tmp_path, final_path


async def save_upload_to_disk(upload_file: UploadFile, destination_path: str):
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with open(destination_path, "wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            f.write(chunk)


def move_file(src: str, dest: str):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.move(src, dest)


def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def validate_file_size(path: str):
    size_mb = get_file_size_mb(path)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise ValueError(
            f"File exceeds {MAX_UPLOAD_SIZE_MB} MB limit (got {size_mb:.2f} MB)"
        )
