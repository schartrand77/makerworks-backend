# app/models/filament.py

from sqlalchemy import Column, Integer, String, Float
from app.models import Base

class Filament(Base):
    __tablename__ = "filaments"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)       # e.g. PLA, PETG
    color = Column(String, nullable=False)      # e.g. Matte Black
    hex = Column(String, nullable=True)         # e.g. #222222
    cost_per_kg = Column(Float, nullable=False) # e.g. 25.99
    texture = Column(String, nullable=True)     # e.g. matte, glossy
    biodegradable = Column(String, nullable=True)  # or Boolean