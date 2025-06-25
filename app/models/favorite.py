# app/models/favorite.py

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


class Favorite(Base):
    __tablename__ = "favorites"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="favorites", lazy="joined")
    model = relationship("Model3D", backref="favorited_by", lazy="joined")