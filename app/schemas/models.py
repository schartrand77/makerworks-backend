# app/schemas/models.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, constr


class ModelBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the model")
    description: Optional[str] = Field(
        None, max_length=1024, description="Optional description of the model"
    )
    is_active: bool = True


class ModelCreate(ModelBase):
    file_url: str = Field(..., description="URL to the uploaded STL/3MF file")
    thumbnail_url: Optional[str] = Field(
        None, description="Optional thumbnail image URL"
    )
    uploaded_by: Optional[str] = Field(
        None, description="User ID of the uploader"
    )
    geometry_hash: Optional[constr(pattern=r"^[a-f0-9]{64}$")] = Field(
        None, description="Optional SHA-256 hash of the model geometry"
    )


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    is_active: Optional[bool] = None
    thumbnail_url: Optional[str] = None
    geometry_hash: Optional[constr(pattern=r"^[a-f0-9]{64}$")] = None
    is_duplicate: Optional[bool] = None


class ModelOut(ModelBase):
    id: int
    file_url: str
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    uploaded_by: Optional[str] = None
    geometry_hash: Optional[str] = None
    is_duplicate: Optional[bool] = None

    class Config:
        from_attributes = True  # Pydantic v2 (formerly orm_mode=True)


class ModelUploadRequest(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the uploaded model")
    description: Optional[str] = Field(
        None, max_length=1024, description="Description of the model"
    )
    file_url: str = Field(..., description="URL to the uploaded file (STL, 3MF, etc.)")
    thumbnail_url: Optional[str] = Field(
        None, description="URL to the thumbnail image"
    )
    uploaded_by: Optional[str] = Field(
        None, description="User ID of the uploader"
    )
    geometry_hash: Optional[constr(pattern=r"^[a-f0-9]{64}$")] = Field(
        None, description="SHA-256 hash of the model geometry"
    )


class ModelUploadResponse(BaseModel):
    id: int
    name: str
    file_url: str
    thumbnail_url: Optional[str] = None
    created_at: datetime
    uploaded_by: Optional[str] = None
    geometry_hash: Optional[str] = None
    is_duplicate: Optional[bool] = None

    class Config:
        from_attributes = True
