from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class SigninRequest(BaseModel):
    email_or_username: str
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    created_at: datetime
    last_login: datetime | None = None
    is_verified: bool

    class Config:
        orm_mode = True


class AuthPayload(BaseModel):
    user: UserOut
    token: str