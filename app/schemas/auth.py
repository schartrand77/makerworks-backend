from typing import Optional
from pydantic import BaseModel, EmailStr, Field, constr


# --------- Token Payload (for internal JWT decoding) ---------

class TokenPayload(BaseModel):
    sub: Optional[int] = Field(
        default=None,
        description="User ID extracted from JWT payload"
    )

    class Config:
        from_attributes = True


# --------- Token Response (for login/signup) ---------

class TokenResponse(BaseModel):
    access_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        example="bearer"
    )

    class Config:
        from_attributes = True


# --------- Auth Input Schemas ---------

class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: constr(min_length=8) = Field(..., example="securepassword123")

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    email: EmailStr = Field(..., example="newuser@example.com")
    username: constr(min_length=3, max_length=32) = Field(..., example="makerpro")
    password: constr(min_length=8) = Field(..., example="supersecurepassword!")

    class Config:
        from_attributes = True


# --------- For Internal DB Bootstrap (optional) ---------

class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="someone@example.com")
    username: constr(min_length=3, max_length=32) = Field(..., example="creator123")
    password: constr(min_length=8) = Field(..., example="hashed_or_raw_pass")

    class Config:
        from_attributes = True