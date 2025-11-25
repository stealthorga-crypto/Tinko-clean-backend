# app/services/email_service.py

import os
import logging
from fastapi import HTTPException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Tinko")

if not SENDGRID_API_KEY:
    logger.error("❌ SENDGRID_API_KEY missing.")
if not FROM_EMAIL:
    logger.error("❌ SENDGRID_FROM_EMAIL missing.")


async def send_email(to_email: str, subject: str, text: str, html: str):
    """Core SendGrid wrapper"""
    if not SENDGRID_API_KEY or not FROM_EMAIL:
        raise HTTPException(500, "Email service not configured")

    try:
        message = Mail(
            from_email=(FROM_EMAIL, FROM_NAME),
            to_emails=to_email,
            subject=subject,
            plain_text_content=text,
            html_content=html,
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        res = sg.send(message)

        logger.info(f"📨 Email sent to {to_email}, Status {res.status_code}")
        return True

    except Exception as e:
        logger.error(f"❌ SendGrid Error: {e}")
        raise HTTPException(500, f"SendGrid failed: {e}")


def build_otp_template(otp: str):
    """Returns plain text + HTML for OTP mail"""

    text = f"Your Tinko verification code is {otp}. Valid for 5 minutes."

    html = f"""
    <div style="font-family:Arial; padding:20px;">
        <h2 style="color:#DE6B06;">Tinko Verification Code</h2>
        <p>Use this OTP to continue:</p>
        <h1 style="font-size:38px; letter-spacing:4px;">{otp}</h1>
        <p>This OTP is valid for <b>5 minutes</b>.</p>
    </div>
    """

    return text, html


async def send_email_otp(to_email: str, otp: str):
    """Send OTP email"""
    text, html = build_otp_template(otp)
    return await send_email(
        to_email=to_email,
        subject="Your Tinko Verification Code",
        text=text,
        html=html,
    )
