# app/routes/__init__.py

from fastapi import APIRouter

# Individual route imports (alphabetical for clarity)
from .admin import router as admin_router
from .auth import router as auth_router
from .cart import router as cart_router
from .checkout import router as checkout_router
from .discord import router as discord_router
from .filaments import router as filaments_router
from .favorites import router as favorites_router
from .models import router as models_router
from .system import router as system_router
from .upload import router as upload_router
from .users import router as users_router

# Central API router
router = APIRouter()

# Register each router under a clean prefix
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(cart_router, prefix="/cart", tags=["cart"])
router.include_router(checkout_router, prefix="/checkout", tags=["checkout"])
router.include_router(discord_router, prefix="/discord", tags=["discord"])
router.include_router(filaments_router, prefix="/filaments", tags=["filaments"])
router.include_router(favorites_router, prefix="/favorites", tags=["favorites"])
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(system_router, prefix="/system", tags=["system"])
router.include_router(upload_router, prefix="/upload", tags=["upload"])
router.include_router(users_router, prefix="/users", tags=["users"])