# app/routes/checkout.py

import logging
import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import Estimate, User
from app.tasks.render import generate_gcode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checkout", tags=["Checkout"])

# ─────────────────────────────────────────────────────────────
# Stripe Setup
# ─────────────────────────────────────────────────────────────
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("DOMAIN", "http://localhost:5173")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not stripe.api_key:
    raise RuntimeError("❌ Missing STRIPE_SECRET_KEY")


# ─────────────────────────────────────────────────────────────
# Pydantic Request Model
# ─────────────────────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    model_id: int = Field(..., description="Uploaded model ID")
    estimate_id: int = Field(..., description="Associated estimate ID")
    total_cost: float = Field(..., description="Final total cost in USD")


# ─────────────────────────────────────────────────────────────
# Create Stripe Checkout Session
# ─────────────────────────────────────────────────────────────
@router.post("/session", summary="Create a Stripe Checkout session")
def create_checkout_session(
    data: CheckoutRequest,
    user: User = Depends(get_user_from_headers),
):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Model #{data.model_id}",
                            "description": f"Estimate ID: {data.estimate_id}",
                        },
                        "unit_amount": int(data.total_cost * 100),  # cents
                    },
                    "quantity": 1,
                }
            ],
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
        logger.info("✅ Stripe session created: %s", session.id)
        return {"id": session.id, "url": session.url}
    except Exception as e:
        logger.error("❌ Stripe session error: %s", e)
        raise HTTPException(status_code=500, detail=f"Stripe error: {e!s}") from e


# ─────────────────────────────────────────────────────────────
# Stripe Webhook Handler
# ─────────────────────────────────────────────────────────────
@router.post("/webhook", summary="Stripe webhook endpoint")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    if not sig or not WEBHOOK_SECRET:
        logger.warning("⚠️ Missing Stripe signature or webhook secret")
        raise HTTPException(
            status_code=400, detail="Missing webhook signature or secret"
        )

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
        logger.info("📡 Webhook event received: %s", event["type"])
    except stripe.error.SignatureVerificationError as e:
        logger.error("❌ Stripe webhook signature invalid")
        raise HTTPException(status_code=400, detail="Invalid Stripe signature") from e

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})

        user_id = metadata.get("user_id")
        model_id = metadata.get("model_id")
        estimate_id = metadata.get("estimate_id")

        logger.info(
            "✅ Payment complete for user %s, model %s, estimate %s",
            user_id,
            model_id,
            estimate_id,
        )

        # ───── Update Estimate in DB ─────
        try:
            est = await db.get(Estimate, int(estimate_id))
            if est:
                est.is_paid = True
                await db.commit()
                logger.info("🧾 Estimate %s marked as paid", estimate_id)
            else:
                logger.warning("⚠️ Estimate %s not found in DB", estimate_id)
        except Exception as e:
            logger.error("❌ DB update failed: %s", e)

        # ───── Enqueue G-code Generation Task ─────
        try:
            generate_gcode.delay(int(model_id), int(estimate_id))
            logger.info("📤 Celery: G-code generation task enqueued")
        except Exception as e:
            logger.error("❌ Celery enqueue failed: %s", e)

    return {"status": "success"}
