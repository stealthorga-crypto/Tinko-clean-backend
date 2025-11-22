# app/services/email_service.py

import os
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# -----------------------------------------------------------------------------
# ENV VARIABLES
# -----------------------------------------------------------------------------
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Tinko")


# -----------------------------------------------------------------------------
# INTERNAL CLIENT CREATOR
# -----------------------------------------------------------------------------
def _get_client() -> Optional[SendGridAPIClient]:
    """Returns a SendGrid client or None if missing API key."""
    if not SENDGRID_API_KEY:
        print("[email_service] SENDGRID_API_KEY not set – email disabled.")
        return None
    try:
        return SendGridAPIClient(SENDGRID_API_KEY)
    except Exception as e:
        print("[email_service] Failed to init SendGrid client:", e)
        return None


# -----------------------------------------------------------------------------
# EARLY ACCESS – CONFIRMATION EMAIL
# -----------------------------------------------------------------------------
def send_early_access_confirmation(to_email: str, company: Optional[str] = None) -> None:
    """Sends confirmation email to user."""
    client = _get_client()
    if not client or not FROM_EMAIL:
        return

    subject = "You’re on the Tinko Early Access List ✅"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#0b0b10; color:#ffffff; padding:24px;">
        <div style="max-width:600px;margin:0 auto;">
          <h1 style="color:#F4511E; margin-bottom:8px;">Tinko</h1>
          <h2 style="margin-top:0;">The Moment That Matters — Saved.</h2>

          <p>Hi,</p>

          <p>
            Thank you for signing up for early access to <strong>Tinko</strong> —
            the payment recovery engine that saves the moment that matters.
          </p>

          <p>
            You’re now part of our priority list. You’ll get:
          </p>

          <ul>
            <li>Early access to the platform</li>
            <li>A guided demo session</li>
            <li>Launch offers & early pricing</li>
          </ul>

          <hr style="border:none;border-top:1px solid #333;margin:24px 0;" />
          <p style="font-size:12px;color:#888;">
            Tinko • A product of Blocks &amp; Loops Technologies Pvt Ltd
          </p>
        </div>
      </body>
    </html>
    """

    message = Mail(
        from_email=(FROM_EMAIL, FROM_NAME),
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        resp = client.send(message)
        print("[email_service] Early access confirmation sent:", resp.status_code)
    except Exception as e:
        print("[email_service] Error sending early access confirmation:", e)


# -----------------------------------------------------------------------------
# EARLY ACCESS – INTERNAL NOTIFICATION
# -----------------------------------------------------------------------------
def send_early_access_internal_alert(user_email: str, company: Optional[str] = None) -> None:
    """Sends internal alert email to you (contact@tinko.in)."""
    client = _get_client()
    if not client or not FROM_EMAIL:
        return

    internal_to = os.getenv("TINKO_INTERNAL_ALERT_EMAIL", "contact@tinko.in")
    subject = "[Tinko] New Early Access Signup"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#0b0b10; color:#ffffff; padding:24px;">
        <div style="max-width:600px;margin:0 auto;">
          <h2>New Early Access Signup</h2>
          <p><strong>Email:</strong> {user_email}</p>
          <p><strong>Company:</strong> {company or "Not provided"}</p>
        </div>
      </body>
    </html>
    """

    message = Mail(
        from_email=(FROM_EMAIL, FROM_NAME),
        to_emails=internal_to,
        subject=subject,
        html_content=html_content,
    )

    try:
        resp = client.send(message)
        print("[email_service] Internal early access alert sent:", resp.status_code)
    except Exception as e:
        print("[email_service] Error sending internal early access alert:", e)


# -----------------------------------------------------------------------------
# FAILED PAYMENT ALERT (MAIN PRODUCT FEATURE)
# -----------------------------------------------------------------------------
def send_failed_payment_alert(
    to_email: str,
    customer_name: Optional[str],
    amount: Optional[str],
    order_id: Optional[str],
    retry_url: str,
    merchant_name: str = "Your Store",
) -> None:
    """Sends recovery email to customer for failed payment."""
    client = _get_client()
    if not client or not FROM_EMAIL:
        return

    subject = "Complete Your Payment Securely"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#0b0b10; color:#ffffff; padding:24px;">
        <div style="max-width:600px;margin:0 auto;">
          <h1 style="color:#F4511E; margin-bottom:8px;">{merchant_name}</h1>
          <h2 style="margin-top:0;">Your Payment Didn’t Go Through</h2>

          <p>Hi {customer_name or ""},</p>

          <p>
            Your recent attempt to pay <strong>{amount or ""}</strong>
            for order <strong>{order_id or ""}</strong> didn’t go through.
          </p>

          <p>No amount was deducted. You can complete your payment below:</p>

          <a href="{retry_url}"
             style="display:inline-block;margin-top:20px;padding:14px 22px;
                    background-color:#F4511E;color:#ffffff;text-decoration:none;
                    border-radius:6px;font-weight:bold;">
            Retry Payment
          </a>

          <hr style="border:none;border-top:1px solid #333;margin:24px 0;">
          <p style="font-size:12px;color:#888;">
            Powered by Tinko • Recovering failed payments automatically
          </p>
        </div>
      </body>
    </html>
    """

    message = Mail(
        from_email=(FROM_EMAIL, FROM_NAME),
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        resp = client.send(message)
        print("[email_service] Failed payment email sent:", resp.status_code)
    except Exception as e:
        print("[email_service] Error sending failed payment email:", e)


# -----------------------------------------------------------------------------
# EMAIL OTP – FOR LOGIN
# -----------------------------------------------------------------------------
def send_email_otp(to_email: str, otp: str) -> None:
    """Sends OTP to user email for login authentication."""
    client = _get_client()
    if not client or not FROM_EMAIL:
        print("[email_service] OTP email skipped (no client).")
        return

    subject = "Your Tinko Login OTP"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding:24px;">
        <div style="max-width:600px;margin:0 auto;">
          <h2>Your Tinko Login OTP</h2>

          <p>Your login code is:</p>

          <h1 style="letter-spacing:4px;">{otp}</h1>

          <p>This OTP is valid for 5 minutes.</p>

          <hr style="margin:24px 0;">
          <p style="font-size:12px;color:#888;">
            Tinko • Blocks & Loops Technologies Pvt Ltd
          </p>
        </div>
      </body>
    </html>
    """

    message = Mail(
        from_email=(FROM_EMAIL, FROM_NAME),
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        resp = client.send(message)
        print("[email_service] OTP email sent:", resp.status_code)
    except Exception as e:
        print("[email_service] Failed to send OTP email:", e)
