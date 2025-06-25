# app/models/filament_pricing.py

from sqlalchemy import Column, Integer, String, Float
from app.db import Base

class FilamentPricing(Base):
    __tablename__ = "filament_pricing"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "PLA MATTE"
    density = Column(Float, nullable=False)             # g/mm³
    price_per_gram = Column(Float, nullable=False)      # USD
    custom_text_fee = Column(Float, default=2.00)       # Optional surcharge