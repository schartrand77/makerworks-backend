from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# --------- Core User Schemas ---------

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str = Field(min_length=8, description="Must be at least 8 characters")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int  # Postgres integer ID assumed
    role: Literal['admin', 'user']
    is_active: bool = True

    class Config:
        from_attributes = True


# --------- Update Schemas ---------

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=140)
    language: Optional[Literal['en', 'fr', 'es', 'de', 'zh', 'ja']] = None

    class Config:
        from_attributes = True


class EmailUpdate(BaseModel):
    new_email: EmailStr


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class RoleUpdate(BaseModel):
    role: Literal['admin', 'user']
    user_id: int


# --------- Auth Schemas ---------

class TokenPayload(BaseModel):
    sub: Optional[int] = None  # user_id


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------- Utility Schemas ---------

class UsernameAvailability(BaseModel):
    available: bool


class BioUpdate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=140)


class LanguagePreference(BaseModel):
    language: Literal['en', 'fr', 'es', 'de', 'zh', 'ja']
    
    
class ModelOut(BaseModel):
    id: int
    name: str
    uploader: str
    uploaded_at: datetime
    preview_image: str

    class Config:
        from_attributes = True