from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl, field_serializer


class UserOut(BaseModel):
    """
    Outbound user schema for API responses.
    Aligns with frontend UserProfile type.
    """

    id: UUID
    email: EmailStr
    username: str
    name: str | None
    bio: str | None
    role: str
    is_verified: bool
    created_at: datetime
    last_login: datetime | None
    avatar_url: HttpUrl | None
    thumbnail_url: HttpUrl | None  # NEW: optional thumbnail if stored
    avatar_updated_at: datetime | None
    language: str | None  # NEW: optional user language preference

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info) -> str:
        return str(v)

    @field_serializer("created_at", "last_login", "avatar_updated_at")
    def serialize_datetimes(self, dt: datetime | None, _info) -> str | None:
        return dt.isoformat() if dt else None

    model_config = {
        "from_attributes": True,
        "json_encoders": {UUID: lambda v: str(v), datetime: lambda dt: dt.isoformat()},
    }


class UpdateUserProfile(BaseModel):
    """
    Inbound user profile updates.
    Fields are optional and validated.
    """
    name: str | None
    bio: str | None
    language: str | None  # NEW: allow updating language
    avatar_url: HttpUrl | None = None  # Optional frontend-provided override

    model_config = {"extra": "forbid"}


class AvatarUploadResponse(BaseModel):
    status: str
    avatar_url: HttpUrl
    thumbnail_url: HttpUrl | None = None
    uploaded_at: datetime
