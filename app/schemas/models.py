from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


class ModelOut(BaseModel):
    id: int
    name: str
    uploader: str
    uploaded_at: datetime
    preview_image: HttpUrl | None = None
    dimensions: dict[str, float] | None = None
    volume_cm3: float | None = None
    tags: list[str] = []
    face_count: int | None = None
    role: Literal["user", "admin"] | None = "user"
    description: str | None = None
    category: str | None = "uncategorized"
    model_config = {"from_attributes": True}


class ModelUploadRequest(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] = []
    category: str | None = "uncategorized"
    model_config = {"from_attributes": True}


class ModelUploadResponse(BaseModel):
    id: int
    name: str
    preview_image: HttpUrl | None = None
    uploaded_at: datetime
    model_config = {"from_attributes": True}
