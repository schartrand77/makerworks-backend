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
    Index,
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

    geometry_hash = Column(String(64), unique=True, index=True, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending | processing | ready | error

    uploaded_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)

    avatar = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    language = Column(String, default="en")  # ISO code
    theme = Column(String, default="system")  # light/dark/system

    role = Column(String, default="user")  # user or admin
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

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

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)

    def __repr__(self):
        return f"<Favorite user_id={self.user_id} model_id={self.model_id}>"

# ========================
# 🧵 Filament Library
# ========================
class Filament(Base):
    __tablename__ = "filaments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    group = Column(String, nullable=False)  # e.g. PLA, PLA MATTE
    price_per_kg = Column(Float, nullable=False)
    color_hex = Column(String, nullable=False)  # hex string like #FFFFFF
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Filament id={self.id} name={self.name} group={self.group}>"

# ========================
# 🧾 Estimate Settings
# ========================
class EstimateSettings(Base):
    __tablename__ = "estimate_settings"

    id = Column(Integer, primary_key=True)
    custom_text_base_cost = Column(Float, default=2.00)
    custom_text_cost_per_char = Column(Float, default=0.10)

    def __repr__(self):
        return "<EstimateSettings>"

# ========================
# ✅ Legacy-compatible alias
# ========================
Model3D = ModelMetadata
