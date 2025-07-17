from datetime import timedelta

import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import TokenRequest, TokenResponse, UserOut
from app.core.config import (
    AUTHENTIK_TOKEN_URL,
    AUTHENTIK_CLIENT_ID,
    AUTHENTIK_CLIENT_SECRET,
    AUTHENTIK_USERINFO_URL,
    ALLOWED_REDIRECT_URIS,
)
from app.core.jwt import create_jwt_token
from app.dependencies import get_db

# 🔷 Define router
router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def exchange_token(
    payload: TokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange Authentik OAuth2 code for MakerWorks JWT + user.
    """
    if not payload.code:
        raise HTTPException(status_code=400, detail="Missing code")

    if payload.redirect_uri not in ALLOWED_REDIRECT_URIS:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # Step 1: exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            AUTHENTIK_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": payload.code,
                "redirect_uri": payload.redirect_uri,
                "client_id": AUTHENTIK_CLIENT_ID,
                "client_secret": AUTHENTIK_CLIENT_SECRET,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="No access token received from Authentik",
            )

    # Step 2: fetch userinfo
    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            AUTHENTIK_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

    # Step 3: upsert user in MakerWorks DB
    from app.crud import crud_user

    user = await crud_user.upsert_user_from_authentik(db, userinfo)

    # Step 4: generate MakerWorks JWT
    jwt_token = create_jwt_token(
        data={"user_id": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=60),
    )

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user=UserOut(**user.to_dict()),
    )