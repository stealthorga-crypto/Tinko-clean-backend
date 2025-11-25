from fastapi import APIRouter, HTTPException
from app.schemas_pkg.auth import SendOTPRequest, VerifyOTPRequest, OTPResponse
from app.services.auth_service import generate_otp, save_otp, validate_otp
from app.services.email_service import send_email_otp

router = APIRouter(prefix="/v1/auth", tags=["Auth"])

# -------------------------------------------
# Send OTP
# -------------------------------------------
@router.post("/email/send-otp", response_model=OTPResponse)
async def send_otp_route(request: SendOTPRequest):
    otp = generate_otp()
    save_otp(request.email, otp)

    await send_email_otp(request.email, otp)

    return OTPResponse(
        message="OTP sent successfully",
        email=request.email,
        verified=False
    )

# -------------------------------------------
# Verify OTP
# -------------------------------------------
@router.post("/email/verify-otp", response_model=OTPResponse)
async def verify_otp_route(request: VerifyOTPRequest):
    if validate_otp(request.email, request.otp):
        return OTPResponse(
            message="OTP verified successfully",
            email=request.email,
            verified=True
        )

    raise HTTPException(status_code=400, detail="Invalid or expired OTP")
