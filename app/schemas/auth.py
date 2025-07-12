# app/schemas/auth.py

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ────────────────────────────────────────────────────────────────────────────────
# Base config for all schemas: UUIDs always serialize as strings
# ────────────────────────────────────────────────────────────────────────────────


class MakerWorksBaseModel(BaseModel):
    """
    Base Pydantic model for MakerWorks schemas.

    Enables:
    • ORM mode (from_attributes)
    • JSON-friendly UUID serialization as strings
    """

    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})


# ────────────────────────────────────────────────────────────────────────────────
# JWT Token Payload Schema (decoded from ID/access token)
# ────────────────────────────────────────────────────────────────────────────────


class TokenPayload(MakerWorksBaseModel):
    """
    Represents the claims contained in a decoded JWT.
    """

    sub: str = Field(..., description="Subject (usually user ID or UUID)")
    email: EmailStr = Field(..., description="User's email")
    exp: int = Field(..., description="Expiration timestamp (seconds since epoch)")
    iat: int = Field(..., description="Issued-at timestamp (seconds since epoch)")
    name: str | None = Field(None, description="Full name (optional)")
    preferred_username: str | None = Field(
        None, description="Preferred username (optional)"
    )
    groups: list[str] = Field(
        default_factory=list, description="List of group memberships"
    )


# ────────────────────────────────────────────────────────────────────────────────
# MakerWorks Authenticated User Info (e.g., /auth/me response)
# ────────────────────────────────────────────────────────────────────────────────


class UserOut(MakerWorksBaseModel):
    """
    Public user profile returned in API responses.
    """

    id: str = Field(..., description="User UUID")
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., description="Unique username")
    role: str = Field(..., description="User's role (e.g., admin, user)")
    is_verified: bool = Field(..., description="Whether the account is verified")
    is_active: bool = Field(..., description="Whether the account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: datetime | None = Field(None, description="Last login timestamp")
    avatar: str | None = Field(None, description="URL to user avatar")
    bio: str | None = Field(None, description="Short biography")
    language: str | None = Field(default="en", description="Preferred language code")
    theme: str | None = Field(default="system", description="Preferred UI theme")


# ────────────────────────────────────────────────────────────────────────────────
# Auth Payload — for routes that return { user, token }
# ────────────────────────────────────────────────────────────────────────────────


class AuthPayload(MakerWorksBaseModel):
    """
    Authentication response payload.
    Contains both the authenticated user and a JWT token.
    """

    user: UserOut = Field(..., description="Authenticated user information")
    token: str | None = Field(None, description="JWT access token")


# ────────────────────────────────────────────────────────────────────────────────
# Signup Request Payload
# ────────────────────────────────────────────────────────────────────────────────


class SignupRequest(MakerWorksBaseModel):
    """
    Request payload for creating a new user account.
    """

    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(
        ..., min_length=3, max_length=30, description="Desired unique username"
    )
    password: str = Field(..., min_length=6, description="Account password")


# ────────────────────────────────────────────────────────────────────────────────
# Signin Request Payload
# ────────────────────────────────────────────────────────────────────────────────


class SigninRequest(MakerWorksBaseModel):
    """
    Request payload for signing in with email or username.
    """

    email_or_username: str = Field(..., description="Email or username")
    password: str = Field(..., description="Account password")


# ────────────────────────────────────────────────────────────────────────────────
# Refresh Token Request
# ────────────────────────────────────────────────────────────────────────────────


class RefreshTokenRequest(MakerWorksBaseModel):
    """
    Request payload to refresh an access token.
    """

    refresh_token: str = Field(..., description="Valid refresh token")


# ────────────────────────────────────────────────────────────────────────────────
# Password Reset Request
# ────────────────────────────────────────────────────────────────────────────────


class PasswordResetRequest(MakerWorksBaseModel):
    """
    Request payload to initiate a password reset.
    """

    email: EmailStr = Field(
        ..., description="Email address associated with the account"
    )


# ────────────────────────────────────────────────────────────────────────────────
# Password Reset Confirmation
# ────────────────────────────────────────────────────────────────────────────────


class PasswordResetConfirm(MakerWorksBaseModel):
    """
    Request payload to complete password reset.
    """

    token: str = Field(..., description="Reset token sent to user")
    new_password: str = Field(..., description="New password to set")


# ────────────────────────────────────────────────────────────────────────────────
# Debug Route Schema
# ────────────────────────────────────────────────────────────────────────────────


class DebugAuthPayload(AuthPayload):
    """
    Debug route response payload.
    Includes user info, token, and a debug message.
    """

    debug_message: str | None = Field(
        default="Auth response serialization test passed",
        description="Debug information message",
    )
