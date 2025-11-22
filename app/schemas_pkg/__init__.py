# Expose all schemas so they can be imported as:
# from app.schemas_pkg import XXXXXX

from .auth import (
    UserBase,
    UserCreate,
    UserCreateWithPassword,
    UserLogin,
    GoogleOAuthSignup,
    UserResponse,
    ApiKeyResponse,
    ApiKeyCreate,
    ApiKeyCreateResponse,
    OrganizationResponse,
    TokenResponse,
    TokenPayload,
)

from .recoveries import (
    CustomerIn,
    FailureEventIn,
    FailureEventOut,
    RecoveryLinkRequest,
    RecoveryLinkOut,
    NextRetryAtPatch,
    RecoveryAttemptOut,
    RecoveryAttemptsResponse,
)

__all__ = [
    # auth
    "UserBase",
    "UserCreate",
    "UserCreateWithPassword",
    "UserLogin",
    "GoogleOAuthSignup",
    "UserResponse",
    "ApiKeyResponse",
    "ApiKeyCreate",
    "ApiKeyCreateResponse",
    "OrganizationResponse",
    "TokenResponse",
    "TokenPayload",

    # recoveries
    "CustomerIn",
    "FailureEventIn",
    "FailureEventOut",
    "RecoveryLinkRequest",
    "RecoveryLinkOut",
    "NextRetryAtPatch",
    "RecoveryAttemptOut",
    "RecoveryAttemptsResponse",
]
# Schemas package