# app/schemas_pkg/__init__.py

# OTP-related schemas
from .auth import (
    SendOTPRequest,
    VerifyOTPRequest,
    OTPResponse,
)

# Recovery schemas
from .recoveries import (
    RecoveryLinkRequest,
    RecoveryLinkOut,
    RecoveryAttemptOut,
    RecoveryAttemptsResponse,
)

__all__ = [
    # OTP
    "SendOTPRequest",
    "VerifyOTPRequest",
    "OTPResponse",

    # Recoveries
    "RecoveryLinkRequest",
    "RecoveryLinkOut",
    "RecoveryAttemptOut",
    "RecoveryAttemptsResponse",
]
