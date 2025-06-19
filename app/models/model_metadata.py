# app/models/model_metadata.py

from sqlalchemy import Column, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models import Base

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    volume_mm3 = Column(Float, nullable=False)
    dimensions_mm = Column(JSON, nullable=False)
    face_count = Column(Integer, nullable=False)

    # This sets up the reverse relationship to Model3D
    model = relationship("Model3D", back_populates="model_metadata", uselist=False)