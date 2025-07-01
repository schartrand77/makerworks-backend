# app/models/models.py

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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base

# ========================
# 🧠 Model Metadata
# ========================
class ModelMetadata(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    preview_image = Column(String, nullable=True)

    uploader = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False, default="user")

    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(String, default="")
    category = Column(String, default="uncategorized")

    volume_mm3 = Column(Float, nullable=True)
    dimensions_mm = Column(JSON, nullable=True)
    face_count = Column(Integer, nullable=True)

    geometry_hash = Column(String(64), unique=True, index=True, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    status = Column(String, default="pending")

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="models")
    estimates = relationship("Estimate", back_populates="model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ModelMetadata id={self.id} name={self.name} uploader={self.uploader}>"

# ========================
# 👤 Users
# ========================
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4, nullable=False)

    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)

    avatar = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    language = Column(String, default="en")
    theme = Column(String, default="system")

    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    models = relationship("ModelMetadata", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    estimates = relationship("Estimate", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role}>"

# ========================
# ⭐ Favorites
# ========================
class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "model_id", name="uq_user_model_favorite"),
    )

    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_id = Column(String, ForeignKey("models.id"), nullable=False)

    user = relationship("User", back_populates="favorites")
    model = relationship("ModelMetadata")

    def __repr__(self):
        return f"<Favorite user_id={self.user_id} model_id={self.model_id}>"

# ========================
# 🧵 Filament Library
# ========================
class Filament(Base):
    __tablename__ = "filaments"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    group = Column(String, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    color_hex = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    pricing = relationship("FilamentPricing", back_populates="filament", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Filament id={self.id} name={self.name} group={self.group}>"

# ========================
# 💰 Filament Pricing
# ========================
class FilamentPricing(Base):
    __tablename__ = "filament_pricing"

    id = Column(String, primary_key=True)
    filament_id = Column(String, ForeignKey("filaments.id"), nullable=False)
    price_per_gram = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    filament = relationship("Filament", back_populates="pricing")

    def __repr__(self):
        return f"<FilamentPricing filament_id={self.filament_id} price_per_gram={self.price_per_gram}>"

# ========================
# 🧾 Estimate Settings
# ========================
class EstimateSettings(Base):
    __tablename__ = "estimate_settings"

    id = Column(String, primary_key=True)
    custom_text_base_cost = Column(Float, default=2.00)
    custom_text_cost_per_char = Column(Float, default=0.10)

    def __repr__(self):
        return "<EstimateSettings>"

# ========================
# 📜 Audit Logs
# ========================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog user_id={self.user_id} action={self.action}>"

# ========================
# 📦 Estimates
# ========================
class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_id = Column(String, ForeignKey("models.id"), nullable=False)
    estimated_cost = Column(Float, nullable=False)
    estimated_time = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=False)

    user = relationship("User", back_populates="estimates")
    model = relationship("ModelMetadata", back_populates="estimates")

    def __repr__(self):
        return f"<Estimate id={self.id} user_id={self.user_id} model_id={self.model_id}>"

# ========================
# ✅ Legacy-compatible alias
# ========================
Model3D = ModelMetadata
Model = ModelMetadata