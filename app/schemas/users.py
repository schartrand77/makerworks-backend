from typing import Optional, Literal, List
from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr
from datetime import datetime
from enum import Enum

# ─────────────────────────────────────────────────────────────
# Core User Base Schema
# ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: constr(min_length=3, max_length=32) = Field(..., example="printmaster77")

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────────────────────
# Output Schemas
# ─────────────────────────────────────────────────────────────

class UserOut(UserBase):
    id: int = Field(..., example=123)
    role: Literal["admin", "user"] = Field(..., example="user")
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False, example=True)
    created_at: datetime = Field(..., example="2024-01-15T12:00:00Z")
    last_login: Optional[datetime] = Field(None, example="2025-06-13T07:45:00Z")
    avatar: Optional[HttpUrl] = Field(None, example="https://cdn.makerworks.io/avatars/abc123.jpg")
    bio: Optional[constr(max_length=140)] = Field(None, example="Maker. Designer. Print wizard.")
    language: Optional[Literal['en', 'fr', 'es', 'de', 'zh', 'ja']] = Field(default="en")
    theme: Optional[Literal["light", "dark", "system"]] = Field(default="system", example="dark")

    class Config:
        from_attributes = True


class PublicUserOut(BaseModel):
    id: int = Field(..., example=123)
    username: str = Field(..., example="printmaster77")
    avatar: Optional[HttpUrl] = Field(None, example="https://cdn.makerworks.io/avatars/user123.jpg")
    bio: Optional[str] = Field(None, example="I build printer mods.")
    created_at: datetime = Field(..., example="2024-01-15T12:00:00Z")

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────────────────────
# Update Schemas
# ─────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=3, max_length=32)] = None
    bio: Optional[constr(max_length=140)] = None
    language: Optional[Literal['en', 'fr', 'es', 'de', 'zh', 'ja']] = None
    theme: Optional[Literal["light", "dark", "system"]] = Field(None, example="dark")
    avatar: Optional[HttpUrl] = Field(None, example="https://cdn.makerworks.io/avatars/user456.jpg")

    class Config:
        from_attributes = True


class EmailUpdate(BaseModel):
    new_email: EmailStr = Field(..., example="new@example.com")

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    role: Literal['admin', 'user'] = Field(..., example="admin")
    user_id: int = Field(..., example=42)

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────────────────────
# Utility Schemas
# ─────────────────────────────────────────────────────────────

class AvatarUpdate(BaseModel):
    avatar_url: Optional[HttpUrl] = Field(
        default=None,
        example="https://cdn.makerworks.io/avatars/user123.jpg",
        description="Direct URL to the new avatar"
    )
    base64_image: Optional[str] = Field(
        default=None,
        description="Base64-encoded image as fallback"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "avatar_url": "https://cdn.makerworks.io/avatars/user123.jpg",
                "base64_image": None
            }
        }


class UsernameAvailability(BaseModel):
    available: bool = Field(..., example=True)

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────────────────────
# Admin Utility Schemas
# ─────────────────────────────────────────────────────────────

class UserAdminAction(str, Enum):
    promote = "promote"
    demote = "demote"
    delete = "delete"
    reset_password = "reset_password"
    view_uploads = "view_uploads"


class UserActionLog(BaseModel):
    id: int
    admin_id: int
    target_user_id: int
    action: UserAdminAction
    timestamp: datetime

    class Config:
        from_attributes = True
