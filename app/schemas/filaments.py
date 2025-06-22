# app/schemas/filaments.py

from pydantic import BaseModel, Field
from typing import Optional


class FilamentCreate(BaseModel):
    name: str
    type: str
    subtype: Optional[str] = None
    surface: Optional[str] = None
    texture: Optional[str] = None

    color: str = Field(..., alias="colorHex")  # hex value from frontend
    color_name: Optional[str] = Field(None, alias="colorName")

    price_per_kg: float = Field(..., alias="pricePerKg")
    currency: Optional[str] = "USD"
    description: Optional[str] = None

    is_active: Optional[bool] = True
    is_biodegradable: Optional[bool] = None


class FilamentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    surface: Optional[str] = None
    texture: Optional[str] = None

    color: Optional[str] = Field(None, alias="colorHex")
    color_name: Optional[str] = Field(None, alias="colorName")

    price_per_kg: Optional[float] = Field(None, alias="pricePerKg")
    currency: Optional[str] = None
    description: Optional[str] = None

    is_active: Optional[bool] = None
    is_biodegradable: Optional[bool] = None


class FilamentOut(BaseModel):
    id: int
    name: str
    type: str
    subtype: Optional[str] = None
    surface: Optional[str] = None
    texture: Optional[str] = None

    color: str = Field(..., alias="colorHex")
    color_name: Optional[str] = Field(None, alias="colorName")

    price_per_kg: float = Field(..., alias="pricePerKg")
    currency: Optional[str] = "USD"
    description: Optional[str] = None

    is_active: Optional[bool] = True
    is_biodegradable: Optional[bool] = None

    class Config:
        from_attributes = True
        populate_by_name = True  # Needed to map aliases on output and input