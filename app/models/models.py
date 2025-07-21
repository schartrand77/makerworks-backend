# app/models/models.py

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Float, ForeignKey,
    UniqueConstraint, Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all models."""
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
    )

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email: str = Column(String, nullable=False, unique=True)
    username: str = Column(String, nullable=False, unique=True)
    hashed_password: str | None = Column(String(128), nullable=True)

    avatar: str | None = Column(String, nullable=True)
    avatar_url: str | None = Column(String, nullable=True)
    avatar_updated_at: datetime | None = Column(DateTime, nullable=True)
    bio: str | None = Column(Text, nullable=True)
    language: str = Column(String, default="en")
    theme: str = Column(String, default="system")

    role: str = Column(String, default="user")
    is_verified: bool = Column(Boolean, default=True)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    last_login: datetime | None = Column(DateTime)

    # Relationships
    models = relationship("ModelMetadata", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    estimates = relationship("Estimate", back_populates="user", cascade="all, delete-orphan")


class Estimate(Base):
    __tablename__ = "estimates"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    model_name: str = Column(String, nullable=False)
    estimated_time: float = Column(Float, nullable=False)
    estimated_cost: float = Column(Float, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="estimates")


class EstimateSettings(Base):
    __tablename__ = "estimate_settings"

    id: str = Column(String, primary_key=True)
    custom_text_base_cost: float = Column(Float, default=2.0, nullable=False)
    custom_text_cost_per_char: float = Column(Float, default=0.1, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    __tablename__ = "favorites"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    model_id: UUID = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    model = relationship("ModelMetadata", back_populates="favorites")


class Filament(Base):
    __tablename__ = "filaments"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    category: str = Column(String, nullable=False)
    type: str = Column(String, nullable=False)
    color_name: str = Column(String, nullable=False)
    color_hex: str = Column(String(7), nullable=False)
    price_per_kg: float = Column(Float, nullable=False)
    surface_texture: str | None = Column(String, nullable=True)
    is_biodegradable: bool = Column(Boolean, default=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


class ModelMetadata(Base):
    __tablename__ = "models"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: str = Column(String, nullable=False)
    description: str | None = Column(Text, nullable=True)
    filename: str = Column(String, nullable=False)
    file_url: str = Column(String, nullable=False)
    thumbnail_url: str | None = Column(String, nullable=True)
    webm_url: str | None = Column(String, nullable=True)  # 👈 NEW

    geometry_hash: str | None = Column(String, nullable=True, index=True)
    is_duplicate: bool = Column(Boolean, default=False)
    uploaded_at: datetime = Column(DateTime, default=datetime.utcnow)

    volume: float | None = Column(Float, nullable=True)
    bbox: dict | None = Column(JSONB, nullable=True)
    faces: int | None = Column(Integer, nullable=True)
    vertices: int | None = Column(Integer, nullable=True)

    user = relationship("User", back_populates="models")
    favorites = relationship("Favorite", back_populates="model", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    action: str = Column(String, nullable=False)
    target: str | None = Column(String, nullable=True)
    description: str | None = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class FilamentPricing(Base):
    __tablename__ = "filament_pricing"

    id: str = Column(String, primary_key=True)
    filament_id: UUID = Column(UUID(as_uuid=True), ForeignKey("filaments.id", ondelete="CASCADE"), nullable=False)
    price_per_gram: float = Column(Float, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
