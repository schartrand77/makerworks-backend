from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr

# ─────────────────────────────────────────────────────────────
# Core User Base Schema
# ─────────────────────────────────────────────────────────────


class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: constr(min_length=3, max_length=32) = Field(..., example="printmaster77")  # type: ignore[valid-type]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
# Output Schemas
# ─────────────────────────────────────────────────────────────


class UserOut(UserBase):
    id: int = Field(..., example=123)
    role: Literal["admin", "user"] = Field(..., example="user")
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False, example=True)
    created_at: datetime = Field(..., example="2024-01-15T12:00:00Z")
    last_login: datetime | None = Field(None, example="2025-06-13T07:45:00Z")
    avatar: HttpUrl | None = Field(
        None, example="https://cdn.makerworks.io/avatars/abc123.jpg"
    )
    bio: constr(max_length=140) | None = Field(  # type: ignore[valid-type]
        None, example="Maker. Designer. Print wizard."
    )
    language: Literal["en", "fr", "es", "de", "zh", "ja"] | None = Field(default="en")
    theme: Literal["light", "dark", "system"] | None = Field(
        default="system", example="dark"
    )

    model_config = {"from_attributes": True}


class PublicUserOut(BaseModel):
    id: int = Field(..., example=123)
    username: str = Field(..., example="printmaster77")
    avatar: HttpUrl | None = Field(
        None, example="https://cdn.makerworks.io/avatars/user123.jpg"
    )
    bio: str | None = Field(None, example="I build printer mods.")
    created_at: datetime = Field(..., example="2024-01-15T12:00:00Z")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
# Update Schemas
# ─────────────────────────────────────────────────────────────


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: constr(min_length=3, max_length=32) | None = None  # type: ignore[valid-type]
    bio: constr(max_length=140) | None = None  # type: ignore[valid-type]
    language: Literal["en", "fr", "es", "de", "zh", "ja"] | None = None
    theme: Literal["light", "dark", "system"] | None = Field(None, example="dark")
    avatar: HttpUrl | None = Field(
        None, example="https://cdn.makerworks.io/avatars/user456.jpg"
    )

    model_config = {"from_attributes": True}


class EmailUpdate(BaseModel):
    new_email: EmailStr = Field(..., example="new@example.com")

    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    role: Literal["admin", "user"] = Field(..., example="admin")
    user_id: int = Field(..., example=42)

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
# Utility Schemas
# ─────────────────────────────────────────────────────────────


class AvatarUpdate(BaseModel):
    avatar_url: HttpUrl | None = Field(
        default=None,
        example="https://cdn.makerworks.io/avatars/user123.jpg",
        description="Direct URL to the new avatar",
    )
    base64_image: str | None = Field(
        default=None, description="Base64-encoded image as fallback"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "avatar_url": "https://cdn.makerworks.io/avatars/user123.jpg",
                "base64_image": None,
            }
        },
    }


class UsernameAvailability(BaseModel):
    available: bool = Field(..., example=True)

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}
