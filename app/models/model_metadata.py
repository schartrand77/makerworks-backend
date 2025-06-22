# app/models/model_metadata.py

from sqlalchemy import Column, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)  # 🛠 link to Model3D
    volume_mm3 = Column(Float, nullable=False)
    dimensions_mm = Column(JSON, nullable=False)
    face_count = Column(Integer, nullable=False)

    model = relationship("Model3D", back_populates="model_metadata")