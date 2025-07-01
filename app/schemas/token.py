# app/schemas/token.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


# ─────────────────────────────────────────────────────────────
# OAuth2 Token Response Schema
# ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    """Returned access token + type (usually 'bearer')"""
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1...")
    token_type: str = Field(..., example="bearer")
    scope: Optional[str] = Field(None, example="openid profile email")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
# Optional Authenticated User Token Data
# ─────────────────────────────────────────────────────────────

class TokenData(BaseModel):
    """Optional JWT token claims (partially decoded)"""
    sub: Optional[str] = Field(None, example="authentik-user-id-uuid")
    email: Optional[EmailStr] = Field(None, example="user@example.com")
    name: Optional[str] = Field(None, example="John Doe")
    preferred_username: Optional[str] = Field(None, example="johnd")
    groups: List[str] = Field(default_factory=list, example=["admin", "user"])
    picture: Optional[str] = Field(None, example="https://cdn.authentik.io/avatar.png")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
# Full Decoded JWT Payload
# ─────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    """Full payload returned when decoding a JWT access token"""
    sub: str = Field(..., example="authentik-user-id-uuid")
    email: EmailStr = Field(..., example="user@example.com")
    name: Optional[str] = Field(None, example="John Doe")
    preferred_username: Optional[str] = Field(None, example="johnd")
    groups: List[str] = Field(default_factory=list, example=["admin", "user"])
    picture: Optional[str] = Field(None, example="https://cdn.authentik.io/avatar.png")
    exp: int = Field(..., example=1719268351, description="Expiration timestamp (UNIX epoch)")
    iat: int = Field(..., example=1719264751, description="Issued-at timestamp (UNIX epoch)")

    model_config = {"from_attributes": True}