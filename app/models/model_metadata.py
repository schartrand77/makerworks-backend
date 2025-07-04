# app/models/model_metadata.py

from sqlalchemy import Column, Float, ForeignKey, JSON, Integer, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, unique=True)

    volume_mm3 = Column(Float, nullable=False)
    dimensions_mm = Column(JSON, nullable=False)  # e.g. {"x": 123.0, "y": 145.0, "z": 100.0}
    face_count = Column(Integer, nullable=False)

    geometry_hash = Column(String, nullable=True, unique=False)  # SHA256 or similar
    is_duplicate = Column(Boolean, default=False, nullable=False)

    model = relationship("Model3D", back_populates="model_metadata", lazy="joined")
