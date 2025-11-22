from __future__ import annotations

import json
import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

try:
    import stripe  # type: ignore
except Exception:  # pragma: no cover
    stripe = None  # type: ignore

from ..deps import get_db
from .. import models


router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def _extract_txn_ref_from_description(desc: str | None) -> str | None:
    if not desc:
        return None
    prefix = "Recovery for "
    if desc.startswith(prefix):
        return desc[len(prefix) :].strip()
    return None


@router.post("/stripe")
async def webhook_stripe(request: Request, db: Session = Depends(get_db), stripe_signature: str | None = Header(default=None, alias="Stripe-Signature")):
    if stripe is None or not os.getenv("STRIPE_WEBHOOK_SECRET"):
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")

    payload = await request.body()
    sig_header = stripe_signature
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)  # type: ignore[attr-defined]
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    etype = event.get("type")
    data = event.get("data", {})
    obj: Dict[str, Any] = data.get("object", {})
    pi_id = obj.get("id")
    desc = obj.get("description")
    txn_ref = _extract_txn_ref_from_description(desc)

    # Store an event row for observability
    if txn_ref:
        txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == txn_ref).first()
    else:
        txn = None

    reason = "payment_succeeded" if etype == "payment_intent.succeeded" else (
        "payment_failed" if etype == "payment_intent.payment_failed" else etype
    )

    fe = models.FailureEvent(
        transaction_id=txn.id if txn else 0,
        gateway="stripe",
        reason=reason or "stripe_event",
        meta={"payment_intent_id": pi_id, "event_type": etype},
    )
    db.add(fe)
    db.commit()

    return {"ok": True}
