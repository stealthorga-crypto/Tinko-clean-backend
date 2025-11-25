import random
import string
import time

# Store OTPs temporarily in memory (Redis later)
OTP_STORE = {}

def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

def save_otp(email: str, otp: str):
    OTP_STORE[email] = {
        "otp": otp,
        "expires_at": time.time() + 300  # expires in 5 minutes
    }

def validate_otp(email: str, otp: str) -> bool:
    data = OTP_STORE.get(email)
    if not data:
        return False

    if time.time() > data["expires_at"]:
        OTP_STORE.pop(email, None)
        return False

    if data["otp"] != otp:
        return False

    OTP_STORE.pop(email, None)
    return True
