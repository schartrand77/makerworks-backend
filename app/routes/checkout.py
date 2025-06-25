# app/routes/checkout.py

import os
import stripe
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.schemas.token import TokenData
from app.dependencies import get_current_user
from app.db.database import get_db
from app.models import User  # Optional: may remove if not querying user directly

router = APIRouter(prefix="/checkout", tags=["Checkout"])

# Load environment secrets
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("DOMAIN", "http://localhost:5173")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


# ─────────────────────────────────────────────────────────────
# Pydantic Request Model
# ─────────────────────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    model_id: int = Field(..., description="Uploaded model ID")
    estimate_id: int = Field(..., description="Associated estimate ID")
    total_cost: float = Field(..., description="Final total cost in USD")


# ─────────────────────────────────────────────────────────────
# Create Checkout Session
# ─────────────────────────────────────────────────────────────
@router.post(
    "/session",
    summary="Create a Stripe Checkout session",
    status_code=status.HTTP_200_OK,
)
def create_checkout_session(
    data: CheckoutRequest,
    user: TokenData = Depends(get_current_user),
):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Model #{data.model_id}",
                        "description": f"Estimate ID: {data.estimate_id}",
                    },
                    "unit_amount": int(data.total_cost * 100),  # Stripe requires cents
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=user.email,
            success_url=f"{DOMAIN}/checkout/success",
            cancel_url=f"{DOMAIN}/checkout/cancel",
            metadata={
                "user_id": str(user.id),
                "model_id": str(data.model_id),
                "estimate_id": str(data.estimate_id),
            },
        )
        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


# ─────────────────────────────────────────────────────────────
# Stripe Webhook Handler
# ─────────────────────────────────────────────────────────────
@router.post(
    "/webhook",
    summary="Stripe webhook endpoint",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    if not sig or not WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Missing webhook signature or secret")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        print("✅ Payment complete:", metadata)

        # TODO: Mark estimate/job as paid in DB
        # TODO: Enqueue Celery job to generate gcode/submit to printer

    return {"status": "success"}