# app/models/__init__.py

from app.db import Base  # ← Use correct base import

# Register all models so SQLAlchemy metadata reflects them during migration
from app.models.user import User
from app.models.model3d import Model3D
from app.models.model_metadata import ModelMetadata
from app.models.favorite import Favorite
from app.models.filament import Filament
from app.models.audit_log import AuditLog
# from app.models.upload import Upload  # ❌ Commented out - model not defined yet

__all__ = [
    "User",
    "Model3D",
    "ModelMetadata",
    "Favorite",
    "Filament",
    "AuditLog",
    # "Upload",  # ❌ Not active
]
