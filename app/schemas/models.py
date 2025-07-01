from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Literal
from datetime import datetime

class ModelOut(BaseModel):
    id: int
    name: str
    uploader: str
    uploaded_at: datetime
    preview_image: Optional[HttpUrl] = None
    dimensions: Optional[Dict[str, float]] = None
    volume_cm3: Optional[float] = None
    tags: List[str] = []
    face_count: Optional[int] = None
    role: Optional[Literal["user", "admin"]] = "user"
    description: Optional[str] = None
    category: Optional[str] = "uncategorized"
    model_config = {"from_attributes": True}

class ModelUploadRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = "uncategorized"
    model_config = {"from_attributes": True}

class ModelUploadResponse(BaseModel):
    id: int
    name: str
    preview_image: Optional[HttpUrl] = None
    uploaded_at: datetime
    model_config = {"from_attributes": True}