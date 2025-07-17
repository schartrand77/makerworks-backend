# app/models/models.py

"""
SQLAlchemy models for MakerWorks backend.
Includes: User, Estimate, Favorite, Filament, ModelMetadata, AuditLog.

Notes:
- `User.authentik_sub` is the stable external identifier from Authentik (`sub` claim in ID token).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from app.db.base import Base


# Base declarative class


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
        UniqueConstraint("authentik_sub", name="uq_user_authentik_sub"),  # renamed + enforced
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    authentik_sub = Column(String, unique=True, nullable=True, index=True)  # external stable ID from Authentik
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String(128), nullable=True)  # optional if only using SSO

    avatar = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    avatar_updated_at = Column(DateTime, nullable=True)
    bio = Column(Text, nullable=True)
    language = Column(String, default="en")
    theme = Column(String, default="system")

    role = Column(String, default="user")
    is_verified = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # relationships
    models = relationship("ModelMetadata", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    estimates = relationship("Estimate", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.pop("password", None)  # ignore plain password
        super().__init__(**kwargs)

    @validates("hashed_password")
    def validate_password(self, key, value):
        if value is None:
            return None
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(value) > 128:
            raise ValueError("Password cannot exceed 128 characters.")
        return value

    def __repr__(self):
        return (
            f"<User id={self.id} username={self.username} authentik_sub={self.authentik_sub} role={self.role}>"
        )


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    model_name = Column(String, nullable=False)
    estimated_time = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="estimates")

    def __repr__(self):
        return f"<Estimate id={self.id} model_name={self.model_name} user_id={self.user_id}>"


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    model = relationship("ModelMetadata", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite id={self.id} user_id={self.user_id} model_id={self.model_id}>"


class Filament(Base):
    __tablename__ = "filaments"

    id = Column(String, primary_key=True)
    category = Column(String, nullable=True)
    type = Column(String, nullable=True)
    name = Column(String, nullable=True)
    color_name = Column(String, nullable=True)
    color_hex = Column(String(7), nullable=True)
    price_per_kg = Column(Float, nullable=False)
    surface_texture = Column(String, nullable=True)
    is_biodegradable = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        if "color" in kwargs and "color_hex" not in kwargs:
            kwargs["color_hex"] = kwargs.pop("color")
        super().__init__(**kwargs)


class FilamentPricing(Base):
    __tablename__ = "filament_pricing"

    id = Column(String, primary_key=True)
    filament_id = Column(String, ForeignKey("filaments.id"), nullable=False)
    price_per_gram = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    filament = relationship("Filament")

    def __repr__(self):
        return f"<FilamentPricing id={self.id} filament_id={self.filament_id} price_per_gram={self.price_per_gram}>"

    def __repr__(self):
        return f"<Filament id={self.id} category={self.category} type={self.type} color={self.color_name}>"


class ModelMetadata(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    geometry_hash = Column(String, nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False)
    volume_mm3 = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="models")
    favorites = relationship("Favorite", back_populates="model", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "uploader" in kwargs and "user_id" not in kwargs:
            uploader = kwargs.pop("uploader")
            kwargs["user_id"] = str(uploader)
        if "user_id" in kwargs and isinstance(kwargs["user_id"], uuid.UUID):
            kwargs["user_id"] = str(kwargs["user_id"])
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<ModelMetadata id={self.id} name={self.name} user_id={self.user_id}>"


class EstimateSettings(Base):
    __tablename__ = "estimate_settings"

    id = Column(String, primary_key=True)
    custom_text_base_cost = Column(Float, default=2.0)
    custom_text_cost_per_char = Column(Float, default=0.1)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<EstimateSettings id={self.id} base_cost={self.custom_text_base_cost} per_char={self.custom_text_cost_per_char}>"
        )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    action = Column(String, nullable=False)              # e.g., CREATE, UPDATE, DELETE
    target = Column(String, nullable=True)              # e.g., model_id or other reference
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog id={self.id} user_id={self.user_id} action={self.action}>"