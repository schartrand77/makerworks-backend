# app/dependencies.py

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import stripe

from app.db.database import get_db
from app.models.models import User
from app.schemas.checkout import CheckoutRequest
from app.config.settings import settings


def parse_group_header(header_value: Optional[str]) -> List[str]:
    """
    Parses a comma-separated header of groups into a list.
    Example: "MakerWorks-Admin,MakerWorks-User" -> ["MakerWorks-Admin", "MakerWorks-User"]
    """
    if not header_value:
        return []
    return [g.strip() for g in header_value.split(",") if g.strip()]


async def get_current_user(
    x_authentik_email: str = Header(..., alias="X-Authentik-Email"),
    x_authentik_groups: Optional[str] = Header(None, alias="X-Authentik-Groups"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Retrieve the current user from the database using Authentik-provided email header.
    Also attach role from group membership.
    """
    result = await db.execute(select(User).where(User.email == x_authentik_email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    groups = parse_group_header(x_authentik_groups)
    if "MakerWorks-Admin" in groups:
        user.role = "admin"
    elif "MakerWorks-User" in groups:
        user.role = "user"
    else:
        user.role = "guest"

    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """
    Raise 403 if user is not admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


async def admin_required(user: User = Depends(get_current_user)) -> User:
    """
    Alias to get_current_admin for lightweight access control.
    """
    return await get_current_admin(user)


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