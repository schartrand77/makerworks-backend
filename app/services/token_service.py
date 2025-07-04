# token_service.py — MakerWorks Backend

from datetime import datetime, timedelta
from jose import jwt
from uuid import uuid4
from app.schemas.token import TokenPayload
from app.schemas.response import TokenResponse
from app.config import settings

ALGORITHM = "HS256"  # Change to RS256 if using public/private keys

def create_token(
    payload: TokenPayload,
    expires_delta: timedelta = timedelta(minutes=60),
    include_refresh: bool = True
) -> TokenResponse:
    now = datetime.utcnow()
    expire = now + expires_delta
    to_encode = payload.dict()

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid4()),  # JWT ID
    })

    access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    if include_refresh:
        refresh_payload = {
            "sub": payload.sub,
            "scope": "refresh_token",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp()),
            "jti": str(uuid4())
        }
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    else:
        refresh_token = None

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds())
    )
