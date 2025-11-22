# app/routers/auth.py

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.auth_service import AuthService
from app.auth_schemas import (
    UserCreateWithPassword,
    UserLogin,
    TokenResponse,
    SendOTPRequest,
    VerifyOTPRequest,
    OTPResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------
# REGISTER (Email + Password)
# ---------------------------------------------------------
@router.post("/register", response_model=OTPResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreateWithPassword, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.
    Sends an OTP to the provided email for verification.
    """
    service = AuthService(db)
    return await service.register_user(payload, request)


# ---------------------------------------------------------
# LOGIN (Email + Password)
# ---------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    Returns JWT access token upon successful authentication.
    """
    service = AuthService(db)
    return await service.login_user(payload.email, payload.password, request)


# ---------------------------------------------------------
# SEND EMAIL OTP
# ---------------------------------------------------------
@router.post("/otp/send", response_model=OTPResponse)
async def send_email_otp(
    payload: SendOTPRequest, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Send OTP to the specified email address.
    Used for email verification or passwordless login.
    """
    service = AuthService(db)
    return await service.send_email_otp(payload.email, request)


# ---------------------------------------------------------
# VERIFY EMAIL OTP
# ---------------------------------------------------------
@router.post("/otp/verify", response_model=TokenResponse)
async def verify_email_otp(
    payload: VerifyOTPRequest, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Verify the OTP sent to the email address.
    Returns JWT access token upon successful verification.
    """
    service = AuthService(db)
    return await service.verify_email_otp(payload.email, payload.otp, request)
