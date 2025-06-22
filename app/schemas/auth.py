from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ────────────────────────────────────────────────────────────────────────────────
# Sign In Request Schema
# ────────────────────────────────────────────────────────────────────────────────
class SignInRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=6, example="strongpassword123")


# ────────────────────────────────────────────────────────────────────────────────
# Token Response Schema
# ────────────────────────────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", example="bearer")


# ────────────────────────────────────────────────────────────────────────────────
# JWT Token Payload Schema (internal use)
# ────────────────────────────────────────────────────────────────────────────────
class TokenPayload(BaseModel):
    sub: str                        # User ID as string
    email: EmailStr
    role: str                       # "user" | "admin"
    exp: int                        # Expiration time (UNIX epoch)
    iat: int                        # Issued at time (UNIX epoch)


# ────────────────────────────────────────────────────────────────────────────────
# Optional: Refresh Token / Reset Flow (future-proofing)
# ────────────────────────────────────────────────────────────────────────────────
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str