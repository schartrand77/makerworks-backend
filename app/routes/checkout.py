# app/routes/checkout.py

import os
import stripe
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.dependencies.auth import get_user_from_headers
from app.db.database import get_db
from app.models import User
from app.models import Estimate
from app.tasks.render import generate_gcode

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
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Model #{data.model_id}",
                        "description": f"Estimate ID: {data.estimate_id}",
                    },
                    "unit_amount": int(data.total_cost * 100),  # cents
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
        print(f"✅ Stripe session created: {session.id}")
        return {"id": session.id, "url": session.url}
    except Exception as e:
        print(f"❌ Stripe session error: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


# ─────────────────────────────────────────────────────────────
# Stripe Webhook Handler
# ─────────────────────────────────────────────────────────────
@router.post("/webhook", summary="Stripe webhook endpoint")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    if not sig or not WEBHOOK_SECRET:
        print("⚠️ Missing Stripe signature or webhook secret")
        raise HTTPException(status_code=400, detail="Missing webhook signature or secret")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
        print(f"📡 Webhook event received: {event['type']}")
    except stripe.error.SignatureVerificationError:
        print("❌ Stripe webhook signature invalid")
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})

        user_id = metadata.get("user_id")
        model_id = metadata.get("model_id")
        estimate_id = metadata.get("estimate_id")

        print(f"✅ Payment complete for user {user_id}, model {model_id}, estimate {estimate_id}")

        # ───── Update Estimate in DB ─────
        try:
            est = await db.get(Estimate, int(estimate_id))
            if est:
                est.is_paid = True
                await db.commit()
                print(f"🧾 Estimate {estimate_id} marked as paid")
            else:
                print(f"⚠️ Estimate {estimate_id} not found in DB")
        except Exception as e:
            print(f"❌ DB update failed: {e}")

        # ───── Enqueue G-code Generation Task ─────
        try:
            generate_gcode.delay(int(model_id), int(estimate_id))
            print(f"📤 Celery: G-code generation task enqueued")
        except Exception as e:
            print(f"❌ Celery enqueue failed: {e}")

    return {"status": "success"}