# app/services/auth_service.py

"""
Authentication Service for STEALTH-TINKO
- Email + Password registration & login
- Email OTP (SendGrid) for verification / passwordless login
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import User, MobileOTP, OTPSecurityLog
from app.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.auth_schemas import (
    UserCreateWithPassword,
    UserLogin,
    UserResponse,
    TokenResponse,
    OTPResponse,
    OrganizationResponse,
)
from app.services.email_service import send_email_otp  # ✅ correct name

import secrets
import string
import logging

logger = logging.getLogger(__name__)


# =================================================================
#   OTP HELPERS
# =================================================================

def _generate_otp(length: int = 6) -> str:
    """Generate a secure numeric OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def _otp_expiry() -> datetime:
    """Returns expiry time for OTP (5 minutes from now)."""
    return datetime.utcnow() + timedelta(minutes=5)


# =================================================================
#   AUTH SERVICE
# =================================================================

class AuthService:
    """
    Core auth service.

    NOTE:
      - We reuse MobileOTP table to store OTP for EMAIL as well.
        We simply store the email value in the `mobile_number` column.
      - OTPSecurityLog is used for logging OTP events.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------
    #  REGISTER (email + password)
    # ------------------------------------------------------------
    async def register_user(
        self,
        payload: UserCreateWithPassword,
        request: Request,
    ) -> OTPResponse:
        """
        - Create user with email + password (not yet verified).
        - Send OTP to email for verification.
        - Return generic OTPResponse (no token yet).
        """
        email = payload.email.lower().strip()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        logger.info(f"Register attempt for email={email} from ip={client_ip}")

        # 1) Check if user already exists
        existing = (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists with this email.",
            )

        # 2) Create user record
        hashed_password = get_password_hash(payload.password)

        user = User(
            email=email,
            full_name=payload.full_name,
            hashed_password=hashed_password,
            account_type=payload.account_type or "user",
            is_active=True,
            is_email_verified=False,
            login_count=0,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"New user created with id={user.id} email={user.email}")

        # 3) Generate OTP and send email
        otp = _generate_otp()
        expires_at = _otp_expiry()

        # Store OTP in MobileOTP (using mobile_number field as EMAIL)
        otp_record = MobileOTP(
            mobile_number=email,  # storing email here
            otp_code=otp,
            expires_at=expires_at,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        self.db.add(otp_record)

        # Log security event
        log = OTPSecurityLog(
            email=email,
            ip_address=client_ip,
            user_agent=user_agent,
            action="register_send_otp",
            success=True,
        )
        self.db.add(log)
        self.db.commit()

        # ✅ Use SendGrid to send OTP email
        await send_email_otp(email, otp)

        return OTPResponse(
            message="Registration successful. OTP sent to your email.",
            success=True,
            details={
                "expires_in_seconds": 300,
                "email": email,
            },
        )

    # ------------------------------------------------------------
    #  LOGIN (email + password)
    # ------------------------------------------------------------
    async def login_user(
        self,
        email: str,
        password: str,
        request: Request,
    ) -> TokenResponse:
        """
        Email + password login. Returns JWT token.
        """
        email = email.lower().strip()
        client_ip = request.client.host if request.client else "unknown"

        user = (
            self.db.query(User)
            .filter(and_(User.email == email, User.is_active == True))
            .first()
        )

        if not user or not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        # update login stats
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"User login success user_id={user.id} ip={client_ip}")

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        organization: Optional[OrganizationResponse] = None

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            organization=organization,
        )

    # ------------------------------------------------------------
    #  SEND EMAIL OTP (for login / verify)
    # ------------------------------------------------------------
    async def send_email_otp(
        self,
        email: str,
        request: Request,
    ) -> OTPResponse:
        """
        Sends email OTP for:
          - passwordless login
          - email verification
        Does NOT create the user; assumes user already exists.
        """
        email = email.lower().strip()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        user = (
            self.db.query(User)
            .filter(and_(User.email == email, User.is_active == True))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active user found for this email.",
            )

        # Invalidate previous unused OTPs for this email
        self.db.query(MobileOTP).filter(
            and_(
                MobileOTP.mobile_number == email,
                MobileOTP.is_used == False,
            )
        ).update({"is_used": True})

        otp = _generate_otp()
        expires_at = _otp_expiry()

        otp_record = MobileOTP(
            mobile_number=email,
            otp_code=otp,
            expires_at=expires_at,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        self.db.add(otp_record)

        log = OTPSecurityLog(
            email=email,
            ip_address=client_ip,
            user_agent=user_agent,
            action="send_email_otp",
            success=True,
        )
        self.db.add(log)
        self.db.commit()

        # ✅ Send email via SendGrid
        await send_email_otp(email, otp)

        return OTPResponse(
            message="OTP sent to your email.",
            success=True,
            details={
                "expires_in_seconds": 300,
                "email": email,
            },
        )

    # ------------------------------------------------------------
    #  VERIFY EMAIL OTP
    # ------------------------------------------------------------
    async def verify_email_otp(
        self,
        email: str,
        otp: str,
        request: Request,
    ) -> TokenResponse:
        """
        Verify the email OTP.
        - Marks OTP as used.
        - Marks user email as verified (if not already).
        - Returns JWT token.
        """
        email = email.lower().strip()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # Get latest unused OTP for this email
        otp_record: Optional[MobileOTP] = (
            self.db.query(MobileOTP)
            .filter(
                and_(
                    MobileOTP.mobile_number == email,
                    MobileOTP.otp_code == otp,
                    MobileOTP.is_used == False,
                )
            )
            .order_by(MobileOTP.created_at.desc())
            .first()
        )

        if not otp_record:
            # log failed attempt
            fail_log = OTPSecurityLog(
                email=email,
                ip_address=client_ip,
                user_agent=user_agent,
                action="verify_email_otp",
                success=False,
            )
            self.db.add(fail_log)
            self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP.",
            )

        # Check expiry
        if otp_record.expires_at < datetime.utcnow():
            otp_record.is_used = True
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired.",
            )

        # Mark OTP as used
        otp_record.is_used = True
        otp_record.attempts = (otp_record.attempts or 0) + 1

        # Find user
        user = (
            self.db.query(User)
            .filter(and_(User.email == email, User.is_active == True))
            .first()
        )
        if not user:
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for this email.",
            )

        # Mark email as verified, update login stats
        user.is_email_verified = True
        if hasattr(user, "email_verified_at"):
            user.email_verified_at = datetime.utcnow()
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1

        success_log = OTPSecurityLog(
            email=email,
            ip_address=client_ip,
            user_agent=user_agent,
            action="verify_email_otp",
            success=True,
        )
        self.db.add(success_log)
        self.db.commit()
        self.db.refresh(user)

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            organization=None,
        )
