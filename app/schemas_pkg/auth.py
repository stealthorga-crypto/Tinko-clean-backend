from pydantic import BaseModel, EmailStr

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class OTPResponse(BaseModel):
    message: str
    email: EmailStr
    verified: bool = False
