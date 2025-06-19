from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Re-export all models here
from .user import User
from .model3d import Model3D
from .model_metadata import ModelMetadata
from .filament import Filament
from .favorite import Favorite  # ✅ Add this