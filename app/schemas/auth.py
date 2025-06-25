from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ────────────────────────────────────────────────────────────────────────────────
# JWT Token Payload Schema (decoded from ID/access token)
# ────────────────────────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str                                # User ID (subject claim)
    email: EmailStr                         # Primary email
    exp: int                                # Expiration timestamp (UNIX epoch)
    iat: int                                # Issued-at timestamp (UNIX epoch)
    name: Optional[str] = None              # Full name (if provided)
    preferred_username: Optional[str] = None  # Username used for display
    groups: List[str] = []                  # Group memberships (e.g. ['admin'])


# ────────────────────────────────────────────────────────────────────────────────
# MakerWorks Authenticated User Info (returned by /auth/me)
# ────────────────────────────────────────────────────────────────────────────────

class AuthResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: str
    is_verified: bool


# ────────────────────────────────────────────────────────────────────────────────
# Optional: Refresh Token / Password Reset Flow (future support)
# ────────────────────────────────────────────────────────────────────────────────

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str