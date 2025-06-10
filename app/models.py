from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


# ========================
# 🧠 Model Metadata
# ========================

class ModelMetadata(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    preview_image = Column(String, nullable=True)

    uploader = Column(String, nullable=False)  # user ID from JWT
    role = Column(String, nullable=False, default="user")

    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(String, default="")
    category = Column(String, default="uncategorized")

    volume_mm3 = Column(Float, nullable=True)
    dimensions_mm = Column(JSON, nullable=True)  # {"x": ..., "y": ..., "z": ...}
    face_count = Column(Integer, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow)


# ========================
# 👤 Users
# ========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # user or admin
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)


# ========================
# ⭐ Favorites
# ========================

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)


# ========================
# 🧵 Filament Library
# ========================

class Filament(Base):
    __tablename__ = "filaments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    group = Column(String, nullable=False)  # e.g. PLA, PLA MATTE
    price_per_kg = Column(Float, nullable=False)
    color_hex = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)


# ========================
# 🧾 Estimate Settings
# ========================

class EstimateSettings(Base):
    __tablename__ = "estimate_settings"

    id = Column(Integer, primary_key=True)
    custom_text_base_cost = Column(Float, default=2.00)
    custom_text_cost_per_char = Column(Float, default=0.10)