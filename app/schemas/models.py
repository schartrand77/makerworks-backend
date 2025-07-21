from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, HttpUrl


class ModelOut(BaseModel):
    id: int
    name: str
    uploader: str
    uploaded_at: datetime
    preview_image: Optional[HttpUrl] = None
    webm_url: Optional[HttpUrl] = None   # ← Added for turntable preview
    dimensions: Optional[dict[str, float]] = None
    volume_cm3: Optional[float] = None
    tags: list[str] = []
    face_count: Optional[int] = None
    role: Optional[Literal["user", "admin"]] = "user"
    description: Optional[str] = None
    category: Optional[str] = "uncategorized"

    model_config = {"from_attributes": True}


class ModelUploadRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tags: list[str] = []
    category: Optional[str] = "uncategorized"

    model_config = {"from_attributes": True}


class ModelUploadResponse(BaseModel):
    id: int
    name: str
    preview_image: Optional[HttpUrl] = None
    webm_url: Optional[HttpUrl] = None   # ← Added here as well
    uploaded_at: datetime

    model_config = {"from_attributes": True}
