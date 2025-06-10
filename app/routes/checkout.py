# routes/checkout.py
import os, stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth import get_current_user, TokenData

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("DOMAIN")

class CheckoutRequest(BaseModel):
    model_id: int
    estimate_id: int
    total_cost: float

@router.post("/session")
def create_checkout_session(data: CheckoutRequest, user: TokenData = Depends(get_current_user)):
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
                    "unit_amount": int(data.total_cost * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=user.email,
            success_url=f"{DOMAIN}/checkout/success",
            cancel_url=f"{DOMAIN}/checkout/cancel",
            metadata={
                "user_id": user.id,
                "model_id": data.model_id,
                "estimate_id": data.estimate_id
            }
        )
        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("✅ Payment complete:", session.get("metadata"))
        # Add logic to mark job as paid, create print job, etc.

    return {"status": "success"}