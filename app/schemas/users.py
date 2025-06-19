from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr
from datetime import datetime

# --------- Core User Schemas ---------

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: constr(min_length=3, max_length=32) = Field(..., example="printmaster77")

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: constr(min_length=8) = Field(..., example="strongpassword123")


class UserRegister(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=32)
    password: constr(min_length=8)

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: constr(min_length=8) = Field(..., example="strongpassword123")

    class Config:
        from_attributes = True


# --------- Output Schemas ---------

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

    class Config:
        from_attributes = True


class PublicUserOut(BaseModel):
    id: int = Field(..., example=123)
    username: str = Field(..., example="printmaster77")
    created_at: datetime = Field(..., example="2024-01-15T12:00:00Z")

    class Config:
        from_attributes = True


# --------- Update Schemas ---------

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=3, max_length=32)] = None
    bio: Optional[constr(max_length=140)] = None
    language: Optional[Literal['en', 'fr', 'es', 'de', 'zh', 'ja']] = None
    theme: Optional[Literal["light", "dark", "system"]] = Field(None, example="dark")

    class Config:
        from_attributes = True


class EmailUpdate(BaseModel):
    new_email: EmailStr = Field(..., example="new@example.com")

    class Config:
        from_attributes = True


class PasswordUpdate(BaseModel):
    current_password: constr(min_length=8) = Field(..., example="oldpass123")
    new_password: constr(min_length=8) = Field(..., example="newpass456")

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    role: Literal['admin', 'user'] = Field(..., example="admin")
    user_id: int = Field(..., example=42)

    class Config:
        from_attributes = True


# --------- Utility Schemas ---------

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