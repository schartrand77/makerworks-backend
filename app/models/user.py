from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship  # ✅ required for uploads = relationship(...)
from datetime import datetime
from app.models import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    uploads = relationship("Model3D", back_populates="uploader")  # ✅

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String, default="user")  # "user" or "admin"