from .auth import admin_required, get_current_admin_user, get_current_user
from .db import get_db

get_current_admin = get_current_admin_user

__all__ = [
    "admin_required",
    "get_current_admin",  # Include alias
    "get_current_admin_user",
    "get_current_user",
    "get_db",
]
