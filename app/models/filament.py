# app/models/filament.py

from sqlalchemy import Column, Integer, String, Float, Boolean
from app.db.database import Base


class Filament(Base):
    __tablename__ = "filaments"

    id = Column(Integer, primary_key=True, index=True)

    # Required by frontend (mapped in schemas)
    name = Column(String, nullable=False)                # Filament name (e.g. PLA Matte)
    type = Column(String, nullable=False)                # Category (e.g. PLA, PETG)
    surface = Column(String, nullable=True)              # Surface label (e.g. Matte, Glossy)
    color = Column(String, nullable=False)               # Hex code (e.g. #FFCC00) → mapped as colorHex
    color_name = Column(String, nullable=True)           # Display name (e.g. “Lemon Yellow”) → colorName
    price_per_kg = Column(Float, nullable=False)         # Cost per kg in USD
    currency = Column(String, default="USD")             # ISO 4217 currency code
    description = Column(String, nullable=True)          # Optional description for UI tooltip/help

    # Optional filtering and metadata
    subtype = Column(String, nullable=True)              # Subcategory (e.g. Matte, Silk, Recycled)
    texture = Column(String, nullable=True)              # Physical texture (e.g. glossy, smooth)
    is_biodegradable = Column(Boolean, nullable=True)    # Used for eco filtering
    is_active = Column(Boolean, default=True)            # Used for soft deletion (admin control)
