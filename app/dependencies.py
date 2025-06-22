# app/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError, jwt
import stripe

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas.checkout import CheckoutRequest
from app.schemas.token import TokenData
from app.services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")


def get_current_user_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Decode JWT and return TokenData without hitting the database.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        if user_id is None or email is None:
            raise HTTPException(status_code=401, detail="Missing user ID or email in token")
        return TokenData(id=user_id, email=email, role=role)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode JWT and return full User object from database.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


async def get_current_user(user: User = Depends(get_current_user_from_token)) -> User:
    """
    Extract current authenticated user using token and DB.
    """
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """
    Raise 403 if user is not admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


async def admin_required(user: TokenData = Depends(get_current_user_token_data)) -> TokenData:
    """
    Enforces that the current user has an admin role using lightweight token decode.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


async def create_checkout_session(
    data: CheckoutRequest,
    user: User = Depends(get_current_user),
):
    """
    Create a Stripe Checkout session from request data and user info.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(data.total_cost * 100),  # dollars → cents
                        "product_data": {"name": data.description},
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            customer_email=user.email,
            success_url=f"{settings.DOMAIN}/success",
            cancel_url=f"{settings.DOMAIN}/cancel",
        )

        return {"checkout_url": session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")