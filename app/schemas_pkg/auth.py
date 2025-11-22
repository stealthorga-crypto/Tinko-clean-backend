"""
Authentication schemas for STEALTH-TINKO
Supports Gmail OAuth, Mobile OTP, and traditional email/password authentication
"""
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# Base User Models
class UserBase(BaseModel):
    """Base user model with common fields"""
    full_name: Optional[str] = Field(None, max_length=128)
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    preferred_language: Optional[str] = Field("en", max_length=5)
    timezone: Optional[str] = Field("UTC", max_length=50)


class UserCreate(UserBase):
    """User creation schema for signup"""
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    country_code: Optional[str] = Field(None, max_length=5)
    
    @validator('mobile_number')
    def validate_mobile(cls, v):
        if v and not re.match(r'^\+?[1-9]\d{8,14}$', v):
            raise ValueError('Invalid mobile number format. Must be 9-15 digits.')
        return v
    
    @validator('password')
    def validate_password(cls, v, values):
        email = values.get('email')
        mobile = values.get('mobile_number')
        
        # Password is required only if no mobile number (email signup)
        if not mobile and not v:
            raise ValueError('Password is required for email signup')
        
        # If password provided, validate strength
        if v:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
        
        return v
    
    @validator('country_code')
    def validate_country_code(cls, v):
        if v and not re.match(r'^\+[1-9]\d{0,3}$', v):
            raise ValueError('Invalid country code format. Must be +1 to +9999.')
        return v


class UserResponse(UserBase):
    """User response schema"""
    id: int
    auth_provider: str
    account_type: str
    is_active: bool
    mobile_verified: bool
    is_email_verified: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# Authentication Request Models
class EmailPasswordLogin(BaseModel):
    """Traditional email/password login"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class GoogleLoginRequest(BaseModel):
    """Google OAuth login request"""
    access_token: str = Field(..., min_length=10)
    id_token: Optional[str] = None  # For additional verification


class MobileLoginRequest(BaseModel):
    """Mobile number login - sends OTP"""
    mobile_number: str = Field(..., min_length=10, max_length=15)
    country_code: Optional[str] = Field("+91", max_length=5)
    
    @validator('mobile_number')
    def validate_mobile(cls, v):
        # Remove any spaces, dashes, or brackets
        v = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[1-9]\d{8,14}$', v):
            raise ValueError('Invalid mobile number format')
        return v


class VerifyOTPRequest(BaseModel):
    """OTP verification request"""
    mobile_number: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=6, max_length=6)
    
    @validator('otp')
    def validate_otp(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be exactly 6 digits')
        return v


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., min_length=10)


# Response Models
class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None
    user: UserResponse


class OTPResponse(BaseModel):
    """OTP send response"""
    message: str = "OTP sent successfully"
    expires_in: int = 300  # seconds
    mobile_number: str
    can_resend_after: int = 60  # seconds


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True
    details: Optional[Dict[str, Any]] = None


# Validation Models
class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    reset_token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password for authenticated user"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


# Session Management
class SessionInfo(BaseModel):
    """User session information"""
    session_id: str
    user_id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[Dict[str, Any]]
    last_activity: datetime
    expires_at: datetime
    is_active: bool
    
    class Config:
        orm_mode = True


class CreateSessionRequest(BaseModel):
    """Create session request"""
    device_info: Optional[Dict[str, Any]] = None


# Admin/Management Schemas
class UserUpdate(BaseModel):
    """User update schema for admin operations"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    account_type: Optional[str] = None


class UserSearchQuery(BaseModel):
    """User search query parameters"""
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    full_name: Optional[str] = None
    auth_provider: Optional[str] = None
    is_active: Optional[bool] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


# Security Models
class SecurityEvent(BaseModel):
    """Security event logging"""
    user_id: Optional[int] = None
    event_type: str  # login_success, login_failed, otp_sent, etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class RateLimitStatus(BaseModel):
    """Rate limiting status"""
    action: str
    remaining_attempts: int
    reset_time: Optional[datetime] = None
    is_blocked: bool = False


# Google OAuth specific models
class GoogleUserInfo(BaseModel):
    """Google user information from OAuth"""
    sub: str  # Google user ID
    name: str
    email: str
    email_verified: bool
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    locale: Optional[str] = None


# Mobile OTP specific models
class MobileOTPRecord(BaseModel):
    """Mobile OTP record"""
    id: int
    mobile_number: str
    created_at: datetime
    expires_at: datetime
    is_used: bool
    attempts: int
    
    class Config:
        orm_mode = True


# Customer-specific models for payment recovery
class CustomerAuthRequest(BaseModel):
    """Customer authentication for payment recovery"""
    recovery_token: Optional[str] = None  # From recovery link
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None


class GuestSessionRequest(BaseModel):
    """Guest session for payment recovery"""
    recovery_token: str = Field(..., min_length=10)
    transaction_ref: Optional[str] = None


class GuestSessionResponse(BaseModel):
    """Guest session response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes for payment recovery
    session_type: str = "guest"
    recovery_info: Dict[str, Any]  # Transaction details


# Export all schemas
__all__ = [
    "UserBase", "UserCreate", "UserResponse", "EmailPasswordLogin",
    "GoogleLoginRequest", "MobileLoginRequest", "VerifyOTPRequest",
    "RefreshTokenRequest", "TokenResponse", "OTPResponse", "MessageResponse",
    "PasswordResetRequest", "PasswordResetConfirm", "ChangePasswordRequest",
    "SessionInfo", "CreateSessionRequest", "UserUpdate", "UserSearchQuery",
    "SecurityEvent", "RateLimitStatus", "GoogleUserInfo", "MobileOTPRecord",
    "CustomerAuthRequest", "GuestSessionRequest", "GuestSessionResponse"
]