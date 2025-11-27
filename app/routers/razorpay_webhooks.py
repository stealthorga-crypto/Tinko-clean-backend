"""
Razorpay webhooks: POST /v1/webhooks/razorpay
- Validates HMAC signature using RAZORPAY_WEBHOOK_SECRET
- Idempotent via PspEvent table keyed by provider:event:payment_id|order_id
- On payment.captured|order.paid, marks related recovery attempt as completed
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import PspEvent, Transaction
from app import models
from app.services.payments.razorpay_adapter import RazorpayAdapter
from app.analytics.sink import emit

router = APIRouter(tags=["Razorpay Webhooks"])


@router.post("/razorpay", include_in_schema=True)
async def webhook_razorpay(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        adapter = RazorpayAdapter()
        event = adapter.validate_webhook(body, signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    etype = event.get("event") or event.get("event_type")
    payload_obj = event.get("payload") or {}

    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    if "payment" in payload_obj:
        payment = payload_obj.get("payment", {}).get("entity", {})
        payment_id = payment.get("id")
        order_id = payment.get("order_id")
    elif "order" in payload_obj:
        order = payload_obj.get("order", {}).get("entity", {})
        order_id = order.get("id")

    uid = None
    if etype and (payment_id or order_id):
        uid = f"razorpay:{etype}:{payment_id or order_id}"

    if uid:
        # Idempotency check
        existing = db.query(PspEvent).filter(PspEvent.psp_event_id == uid).first()
        if existing:
            return {"status": "ok", "idempotent": True}
        rec = PspEvent(provider="razorpay", event_type=etype or "unknown", psp_event_id=uid, payload=event)
        db.add(rec)
        db.flush()

    if order_id:
        txn = db.query(Transaction).filter(Transaction.razorpay_order_id == order_id).first()
        if not txn:
            # Try to match by receipt/transaction_ref
            receipt = (
                payload_obj.get("order", {}).get("entity", {}).get("receipt")
                or payload_obj.get("payment", {}).get("entity", {}).get("notes", {}).get("receipt")
            )
            if receipt:
                txn = db.query(Transaction).filter(Transaction.transaction_ref == receipt).first()
        if txn:
            # Idempotent payment mapping
            if payment_id and txn.razorpay_payment_id == payment_id:
                return {"status": "ok", "idempotent": True}
            if etype in ("payment.captured", "order.paid"):
                txn.razorpay_payment_id = payment_id or txn.razorpay_payment_id
                attempt = (
                    db.query(models.RecoveryAttempt)
                    .filter(
                        (models.RecoveryAttempt.transaction_id == txn.id)
                        | (models.RecoveryAttempt.transaction_ref == txn.transaction_ref)
                    )
                    .order_by(models.RecoveryAttempt.id.desc())
                    .first()
                )
                if attempt and attempt.status != "completed":
                    attempt.status = "completed"
                    attempt.used_at = datetime.utcnow()
                db.commit()
                try:
                    emit(
                        "payment_result",
                        {
                            "provider": "razorpay",
                            "order_id": order_id,
                            "payment_id": payment_id,
                            "transaction_ref": txn.transaction_ref,
                            "org_id": txn.org_id,
                            "status": "success",
                        },
                    )
                except Exception:
                    pass

            elif etype == "payment.failed":
                # Handle Payment Failure -> Trigger Recovery
                txn.razorpay_payment_id = payment_id or txn.razorpay_payment_id
                
                # Check if open attempt exists
                existing_attempt = (
                    db.query(models.RecoveryAttempt)
                    .filter(
                        models.RecoveryAttempt.transaction_id == txn.id,
                        models.RecoveryAttempt.status.in_(["created", "sent", "scheduled"])
                    )
                    .first()
                )
                
                if not existing_attempt:
                    # Create new recovery attempt
                    from secrets import token_urlsafe
                    from datetime import timedelta
                    
                    token = token_urlsafe(16)
                    # Default to 24h expiry
                    expires_at = datetime.utcnow() + timedelta(hours=24)
                    
                    # Determine channel from Org settings or default to email
                    channel = "email"
                    if txn.organization and txn.organization.recovery_channels:
                        # Simple logic: pick first available
                        channel = txn.organization.recovery_channels[0]
                    
                    new_attempt = models.RecoveryAttempt(
                        transaction_id=txn.id,
                        transaction_ref=txn.transaction_ref,
                        channel=channel,
                        token=token,
                        status="created",
                        expires_at=expires_at
                    )
                    db.add(new_attempt)
                    db.commit()
                    db.refresh(new_attempt)
                    
                    # Trigger Retry Task (Synchronous for now)
                    try:
                        from app.tasks.retry_tasks import schedule_retry
                        schedule_retry(new_attempt.id, txn.org_id)
                    except Exception as e:
                        print(f"Failed to trigger retry: {e}")

    return {"status": "ok"}
