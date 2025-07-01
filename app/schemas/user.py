from pydantic import BaseModel, EmailStr, HttpUrl, field_serializer
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    name: Optional[str]
    bio: Optional[str]
    role: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    avatar_url: Optional[HttpUrl]
    avatar_updated_at: Optional[datetime]

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info) -> str:
        return str(v)

    @field_serializer("created_at", "last_login", "avatar_updated_at")
    def serialize_datetimes(self, dt: Optional[datetime], _info) -> Optional[str]:
        return dt.isoformat() if dt else None

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            UUID: lambda v: str(v),
            datetime: lambda dt: dt.isoformat()
        }
    }


class UpdateUserProfile(BaseModel):
    name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[HttpUrl] = None  # Optional frontend-provided override

    model_config = {
        "extra": "forbid"
    }