# app/models/__init__.py

from app.database import Base

# Import all models here to register them with SQLAlchemy metadata
from app.models.user import User
from app.models.model3d import Model3D
from app.models.model_metadata import ModelMetadata
from app.models.favorite import Favorite
from app.models.filament import Filament
from app.models.audit_log import AuditLog
#from app.models.upload import Upload  # ✅ if this model exists

__all__ = [
    "User",
    "Model3D",
    "ModelMetadata",
    "Favorite",
    "Filament",
    "AuditLog",
    #"Upload",  # ✅ included if defined
]