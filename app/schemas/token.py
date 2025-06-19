# app/schemas/token.py

from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    sub: Optional[int] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: int
    email: EmailStr
    role: str
    exp: int
    iat: int