# app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ────────────────────────────────────────────────────────────────────────────────
# Base config for all models: UUIDs should serialize as strings
# ────────────────────────────────────────────────────────────────────────────────

class MakerWorksBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: lambda v: str(v)}  # UUIDs serialize as strings
    )


# ────────────────────────────────────────────────────────────────────────────────
# JWT Token Payload Schema (decoded from ID/access token)
# ────────────────────────────────────────────────────────────────────────────────

class TokenPayload(MakerWorksBaseModel):
    sub: str                                 # User ID (subject claim)
    email: EmailStr                          # Primary email
    exp: int                                 # Expiration timestamp (UNIX epoch)
    iat: int                                 # Issued-at timestamp (UNIX epoch)
    name: Optional[str] = None               # Full name (if provided)
    preferred_username: Optional[str] = None # Username used for display
    groups: List[str] = []                   # Group memberships (e.g. ['admin'])


# ────────────────────────────────────────────────────────────────────────────────
# MakerWorks Authenticated User Info (used in responses like /auth/me)
# ────────────────────────────────────────────────────────────────────────────────

class UserOut(MakerWorksBaseModel):
    id: str  # Serialized UUID (FastAPI returns UUID, Pydantic expects string here)
    email: EmailStr
    username: str
    role: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    language: Optional[str] = "en"
    theme: Optional[str] = "system"


# ────────────────────────────────────────────────────────────────────────────────
# Auth response schema: used for endpoints like /auth/token and /auth/me
# ────────────────────────────────────────────────────────────────────────────────

class AuthResponse(UserOut):
    token: Optional[str] = None  # Optional in case `/me` returns this schema too


# ────────────────────────────────────────────────────────────────────────────────
# Signup Request Payload
# ────────────────────────────────────────────────────────────────────────────────

class SignupRequest(MakerWorksBaseModel):
    email: EmailStr = Field(..., description="User's email")
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6)


# ────────────────────────────────────────────────────────────────────────────────
# Refresh Token Payload
# ────────────────────────────────────────────────────────────────────────────────

class RefreshTokenRequest(MakerWorksBaseModel):
    refresh_token: str


# ────────────────────────────────────────────────────────────────────────────────
# Password Reset Request
# ────────────────────────────────────────────────────────────────────────────────

class PasswordResetRequest(MakerWorksBaseModel):
    email: EmailStr


# ────────────────────────────────────────────────────────────────────────────────
# Password Reset Confirmation
# ────────────────────────────────────────────────────────────────────────────────

class PasswordResetConfirm(MakerWorksBaseModel):
    token: str
    new_password: str


# ────────────────────────────────────────────────────────────────────────────────
# Debug Route Schema: test UUID serialization + user model correctness
# ────────────────────────────────────────────────────────────────────────────────

class DebugAuthResponse(AuthResponse):
    debug_message: Optional[str] = "Auth response serialization test passed"