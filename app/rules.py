from typing import Dict

CODES = {
    "issuer_declined": "issuer_decline",
    "do_not_honor": "issuer_decline",
    "insufficient_funds": "funds",
    "transaction_not_permitted": "issuer_decline",
    "otp_timeout": "auth_timeout",
    "3ds_timeout": "auth_timeout",
    "network_error": "network",
    "upi_pending": "upi_pending",
    # Razorpay-specific codes
    "RZP001_INSUFFICIENT_FUNDS": "funds",
    "RZP_NETWORK_ISSUE": "network",
    "RZP_UPI_INVALID_VPA": "issuer_decline",
    "RZP_CARD_BLOCKED": "issuer_decline",
}

def classify_failure(code: str | None, message: str | None) -> str:
    if code and code in CODES:
        return CODES[code]
    if message:
        m = message.lower()
        if any(k in m for k in ["otp", "3ds", "authentication"]):
            return "auth_timeout"
        if any(k in m for k in ["network", "timeout", "gateway"]):
            return "network"
        if "insufficient" in m:
            return "funds"
        if "upi" in m and "pending" in m:
            return "upi_pending"
    return "unknown"

def next_retry_options(category: str) -> Dict:
    if category in ("network", "auth_timeout"):
        return {"recommendation": "Retry same method with fresh auth",
                "alt": ["upi_collect", "netbanking"],
                "cooldown_seconds": 30}
    if category == "funds":
        return {"recommendation": "Suggest alternate method",
                "alt": ["netbanking", "card_other_bank", "upi_collect"]}
    if category == "issuer_decline":
        return {"recommendation": "Try alternate card or netbanking",
                "alt": ["card_other_bank", "netbanking", "upi_collect"]}
    if category == "upi_pending":
        return {"recommendation": "Poll or provide cancel+alternate",
                "alt": ["netbanking", "card"]}
    return {"recommendation": "Offer alternate method",
            "alt": ["upi_collect", "netbanking", "card"]}
