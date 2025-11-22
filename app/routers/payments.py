from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models
from ..services.payments.stripe_adapter import StripeAdapter
try:
    import stripe  # type: ignore
except Exception:
    stripe = None  # type: ignore


router = APIRouter(prefix="/v1/payments", tags=["payments"])


class CreateIntentIn(BaseModel):
    transaction_ref: str = Field(..., min_length=1, max_length=64)


class CreateIntentOut(BaseModel):
    ok: bool
    data: dict


def _get_txn_by_ref(db: Session, ref: str) -> Optional[models.Transaction]:
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_ref == ref)
        .first()
    )


@router.post("/stripe/intents", response_model=CreateIntentOut)
def create_stripe_intent(body: CreateIntentIn, db: Session = Depends(get_db)):
    if not os.getenv("STRIPE_SECRET_KEY"):
        raise HTTPException(status_code=503, detail="Stripe not configured")

    txn = _get_txn_by_ref(db, body.transaction_ref)
    if not txn or not txn.amount or not txn.currency:
        raise HTTPException(status_code=404, detail="Transaction not found or amount/currency missing")

    adapter = StripeAdapter()
    pi = adapter.create_intent(amount=txn.amount, currency=txn.currency, description=f"Recovery for {txn.transaction_ref}")
    return {"ok": True, "data": {"client_secret": pi.client_secret, "payment_intent_id": pi.id}}


class CreateCheckoutIn(BaseModel):
    transaction_ref: str = Field(..., min_length=1, max_length=64)
    success_url: str = Field(...)
    cancel_url: str = Field(...)


@router.post("/stripe/checkout", response_model=CreateIntentOut)
def create_stripe_checkout(body: CreateCheckoutIn, db: Session = Depends(get_db)):
    if stripe is None or not os.getenv("STRIPE_SECRET_KEY"):
        raise HTTPException(status_code=503, detail="Stripe not configured")

    txn = _get_txn_by_ref(db, body.transaction_ref)
    if not txn or not txn.amount or not txn.currency:
        raise HTTPException(status_code=404, detail="Transaction not found or amount/currency missing")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    session = stripe.checkout.Session.create(  # type: ignore[attr-defined]
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": txn.currency,
                    "product_data": {"name": f"Recovery {txn.transaction_ref}"},
                    "unit_amount": txn.amount,
                },
                "quantity": 1,
            }
        ],
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        payment_intent_data={"description": f"Recovery for {txn.transaction_ref}"},
    )
    return {"ok": True, "data": {"url": session["url"], "id": session["id"]}}
