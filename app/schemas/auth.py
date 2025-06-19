# schemas/auth.py

from pydantic import BaseModel
from app.schemas.users import UserOut  # ✅ FIXED

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "username": "user123",
                    "created_at": "2025-06-16T12:34:56Z",
                    "last_login": "2025-06-16T13:45:00Z",
                    "is_verified": True,
                    "role": "user"
                }
            }
        }