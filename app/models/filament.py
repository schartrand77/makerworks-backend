# app/models/filament.py

from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base


class Filament(Base):
    __tablename__ = "filaments"

    id = Column(Integer, primary_key=True, index=True)

    # Required by frontend
    name = Column(String, nullable=False)                # -> name
    type = Column(String, nullable=False)                # -> type
    surface = Column(String, nullable=True)              # -> surface
    color = Column(String, nullable=False)               # -> colorHex (stored as hex string)
    color_name = Column(String, nullable=True)           # -> colorName
    price_per_kg = Column(Float, nullable=False)         # -> pricePerKg
    currency = Column(String, default="USD")             # -> currency
    description = Column(String, nullable=True)          # -> description

    # Optional filtering/meta
    subtype = Column(String, nullable=True)              # e.g. Matte, Silk
    texture = Column(String, nullable=True)              # physical texture: smooth, glossy, etc.
    is_biodegradable = Column(Boolean, nullable=True)    # for eco filtering
    is_active = Column(Boolean, default=True)            # used for soft-deleting