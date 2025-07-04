from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Literal
from datetime import datetime


class ModelUploadRequest(BaseModel):
    title: str = Field(..., example="Articulated Dragon")
    description: Optional[str] = Field(None, example="A flexible 3D printed dragon with joints.")
    filament_type: Optional[str] = Field(None, example="PLA MATTE")
    geometry_hash: Optional[str] = Field(None, example="abc123xyz")


class ModelUploadResponse(BaseModel):
    id: str = Field(..., example="abc123xyz789")
    name: str = Field(..., example="Articulated Dragon")
    url: str = Field(..., example="https://cdn.makerworks.io/models/abc123xyz.stl")
    uploaded_at: datetime = Field(..., example="2025-06-10T14:23:00Z")


class ModelOut(BaseModel):
    id: int = Field(..., example=101)
    name: str = Field(..., example="Articulated Dragon")
    uploader: str = Field(..., example="stephen_dev")
    uploaded_at: datetime = Field(..., example="2025-06-10T14:23:00Z")

    preview_image: Optional[HttpUrl] = Field(
        None,
        example="https://cdn.makerworks.io/previews/dragon123.png"
    )

    dimensions: Optional[Dict[str, float]] = Field(
        None,
        description="Model bounding box dimensions in mm",
        example={"x": 123.4, "y": 98.7, "z": 65.0}
    )

    volume_cm3: Optional[float] = Field(
        None,
        description="Model volume in cubic centimeters",
        example=154.23
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Descriptive tags for filtering or categorization",
        example=["robot", "mechanical", "mountable"]
    )

    face_count: Optional[int] = Field(
        None,
        description="Number of mesh faces (triangles) in the model",
        example=29834
    )

    role: Optional[Literal["user", "admin"]] = Field(
        default="user",
        description="Uploader role type: user or admin",
        example="user"
    )

    description: Optional[str] = Field(
        None,
        example="A flexible 3D printed dragon with articulating joints.",
        description="User-provided description of the model"
    )

    category: Optional[str] = Field(
        default="uncategorized",
        description="Model category for browsing",
        example="creatures"
    )

    class Config:
        from_attributes = True
