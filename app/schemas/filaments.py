# app/schemas/filaments.py

from pydantic import BaseModel
from typing import Optional


class FilamentCreate(BaseModel):
    name: str
    type: str
    color: str
    price_per_kg: float
    is_active: Optional[bool] = True


class FilamentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    color: Optional[str] = None
    price_per_kg: Optional[float] = None
    is_active: Optional[bool] = None


class FilamentOut(BaseModel):
    id: int
    name: str
    type: str
    color: str
    price_per_kg: float
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True