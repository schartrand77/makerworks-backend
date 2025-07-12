# app/utils/hash_geometry.py

import hashlib


def generate_geometry_hash(volume: float, dimensions: dict, face_count: int) -> str:
    payload = f"{volume}-{dimensions.get('x',0)}-{dimensions.get('y',0)}-{dimensions.get('z',0)}-{face_count}"
    return hashlib.sha256(payload.encode()).hexdigest()
