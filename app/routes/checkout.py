# routes/checkout.py

import os
import stripe
from fastapi import APIRouter, Request, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.utils.auth import get_current_user, TokenData

router = APIRouter(prefix="/api/v1/checkout", tags=["Checkout"])

# Load secrets
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("DOMAIN", "http://localhost:3000")  # Fallback for dev
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


class CheckoutRequest(BaseModel):
    model_id: int = Field(..., description="Uploaded model ID")
    estimate_id: int = Field(..., description="Associated estimate ID")
    total_cost: float = Field(..., description="Final total cost in USD")


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
        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


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

        # TODO: Mark estimate/job as paid
        # TODO: Create print queue task or job entry

    return {"status": "success"}