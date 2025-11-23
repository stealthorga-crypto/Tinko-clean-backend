from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import os
import requests
from typing import Optional

from app.services.email_service import (
    send_early_access_confirmation,
    send_early_access_internal_alert,
)

router = APIRouter(tags=["Early Access"])


class EarlyAccessRequest(BaseModel):
    email: EmailStr
    company: Optional[str] = None


@router.post("/signup")
async def early_access_signup(data: EarlyAccessRequest):
    """
    1) Save signup to Supabase
    2) Send confirmation email to customer
    3) Send internal alert email to team
    """

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not SUPABASE_URL or not SERVICE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration missing")

    insert_url = f"{SUPABASE_URL}/rest/v1/early_access"

    payload = {
        "email": data.email,
        "company": data.company,
    }

    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    # 1️⃣ Save to Supabase
    try:
        r = requests.post(insert_url, json=payload, headers=headers, timeout=10)
        if r.status_code >= 400:
            print("[early_access] Supabase Error:", r.status_code, r.text)
            raise HTTPException(status_code=500, detail="DB insert failed")
    except Exception as e:
        print("[early_access] Supabase Exception:", e)
        raise HTTPException(status_code=500, detail="Could not save signup")

    # 2️⃣ Confirmation email to customer
    try:
        send_early_access_confirmation(
            to_email=data.email,
            company=data.company
        )
    except Exception as e:
        print("[early_access] Confirmation Email Error:", e)

    # 3️⃣ Internal alert email
    try:
        send_early_access_internal_alert(
            user_email=data.email,
            company=data.company
        )
    except Exception as e:
        print("[early_access] Internal Alert Email Error:", e)

    return {"message": "Signup received"}
