import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

ALLOWED_EXTENSIONS = {".stl", ".3mf"}
MAX_UPLOAD_SIZE_MB = 100


def get_file_extension(filename: str) -> str:
    """
    Return the lowercase file extension, including dot.
    """
    return Path(filename).suffix.lower()


def is_valid_model_file(filename: str) -> bool:
    """
    Check if the file has an allowed 3D model extension.
    """
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename with timestamp + uuid.
    """
    ext = get_file_extension(original_filename)
    uid = uuid.uuid4().hex
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
    return f"{timestamp}_{uid}{ext}"


def get_storage_paths(upload_dir: str, filename: str) -> tuple[str, str]:
    """
    Compute temp and final storage paths for a file.
    Returns: (temp_path, final_path)
    """
    upload_dir = Path(upload_dir)
    tmp_path = upload_dir / "tmp" / filename
    final_path = upload_dir / "models" / filename
    return str(tmp_path), str(final_path)


async def save_upload_to_disk(upload_file: UploadFile, destination_path: str) -> None:
    """
    Save an UploadFile to disk at destination_path.
    """
    dest = Path(destination_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            f.write(chunk)


def move_file(src: str, dest: str) -> None:
    """
    Move a file from src to dest, creating dest directories if needed.
    """
    src_path = Path(src)
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_path), str(dest_path))


def get_file_size_mb(path: str) -> float:
    """
    Return the file size in MB.
    """
    return Path(path).stat().st_size / (1024 * 1024)


def validate_file_size(path: str) -> None:
    """
    Raise ValueError if file exceeds MAX_UPLOAD_SIZE_MB.
    """
    size_mb = get_file_size_mb(path)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise ValueError(
            f"File exceeds {MAX_UPLOAD_SIZE_MB} MB limit (got {size_mb:.2f} MB)"
        )
