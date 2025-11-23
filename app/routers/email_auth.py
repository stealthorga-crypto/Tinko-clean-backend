# app/routers/email_auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.supabase_http import send_otp, verify_otp

router = APIRouter(tags=["Auth"])


class SendOTPRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


@router.post("/send-otp")
async def send_otp_route(payload: SendOTPRequest):
    """
    1) Frontend calls this with { email }
    2) Supabase sends a 6-digit OTP email.
    """
    try:
        return await send_otp(payload.email)
    except Exception as e:
        # Bubble the Supabase error in a clean way
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-otp")
async def verify_otp_route(payload: VerifyOTPRequest):
    """
    1) Frontend calls this with { email, otp }
    2) We verify OTP against Supabase
    3) Return Supabase's session (access_token, refresh_token, user, ...)
    """
    try:
        session = await verify_otp(payload.email, payload.otp)
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
