# app/utils/storage.py

import os
from fastapi import UploadFile

def is_valid_model_file(filename: str) -> bool:
    return filename.lower().endswith(('.stl', '.3mf'))

async def save_upload_to_disk(file: UploadFile, dest_path: str) -> None:
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

def generate_unique_filename(original_name: str) -> str:
    from uuid import uuid4
    ext = os.path.splitext(original_name)[-1]
    return f"{uuid4().hex}{ext}"

def get_storage_paths(base_dir: str, filename: str) -> tuple[str, str]:
    tmp_path = os.path.join(base_dir, "tmp", filename)
    final_path = os.path.join(base_dir, "models", filename)
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    return tmp_path, final_path

def move_file(src: str, dest: str) -> None:
    os.rename(src, dest)