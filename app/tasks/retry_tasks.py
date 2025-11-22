# app/tasks/retry_tasks.py

"""
Lightweight placeholder retry task module.
This exists because older routers import from app.tasks.retry_tasks.
We no longer use Celery, so all functions run synchronously.

Later you can plug in:
 - Supabase Edge Functions
 - Cron triggers
 - n8n retry pipeline
 - In-process scheduler
"""

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# PROCESS RETRY QUEUE (used by router /v1/retry/trigger-due)
# ---------------------------------------------------------
def process_retry_queue():
    """
    Placeholder retry queue processor.
    Returns a simple status message.
    """
    logger.info("Retry queue processing started (stub).")

    # In the future: read pending retries from DB and process them.
    processed = 0

    logger.info("Retry queue processing finished (stub).")

    return {
        "message": "Retry queue processed (stub version).",
        "processed": processed
    }


# ---------------------------------------------------------
# UPDATE RETRY POLICY (used by retry_policies router)
# ---------------------------------------------------------
def update_retry_policy(policy_id: int, data: dict):
    """
    Stub: Update retry policy configuration.
    """
    logger.info(f"Updating retry policy (stub): {policy_id}")
    return {
        "message": "Retry policy update not implemented.",
        "policy_id": policy_id,
        "received_data": data
    }


# ---------------------------------------------------------
# SCHEDULE RETRY (used internally by recovery pipeline)
# ---------------------------------------------------------
def schedule_retry(payment_id: int):
    """
    Stub: schedule retry attempt for a failed payment.
    """
    logger.info(f"Scheduling retry (stub) for payment_id={payment_id}")
    return {
        "message": "Retry scheduling not implemented.",
        "payment_id": payment_id
    }
