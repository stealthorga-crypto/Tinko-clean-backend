"""full reset schema

Revision ID: 92ddc575ea20
Revises: 10bb81e42b03
Create Date: 2025-11-15 17:50:53.957529
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '92ddc575ea20'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------
    # FULL RESET — DROP ALL EXISTING TABLES
    # ----------------------------------------------------------
    tables_to_drop = [
        "user_sessions",
        "mobile_otps",
        "email_otps",
        "otp_security_logs",
        "psp_events",
        "recon_logs",
        "retry_policies",
        "notification_logs",
        "recovery_attempts",
        "failure_events",
        "api_keys",
        "transactions",
        "users",
        "organizations",
    ]

    for table in tables_to_drop:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')

    # ----------------------------------------------------------
    # RECREATE SCHEMA — ORGANIZATIONS
    # ----------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ----------------------------------------------------------
    # USERS
    # ----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(128), nullable=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="operator"),
        sa.Column("account_type", sa.String(32), nullable=False, server_default="user"),
        sa.Column("auth_provider", sa.String(50), nullable=False, server_default="email"),
        sa.Column("auth_providers", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("org_id", sa.Integer,
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                  nullable=True, index=True),
        sa.Column("mobile_number", sa.String(20), unique=True, nullable=True, index=True),
        sa.Column("country_code", sa.String(5), nullable=True),
        sa.Column("mobile_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("google_id", sa.String(128), nullable=True, unique=True, index=True),
        sa.Column("google_email", sa.String(255), nullable=True, index=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mobile_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="en"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ----------------------------------------------------------
    # API KEYS
    # ----------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("key_name", sa.String(128), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ----------------------------------------------------------
    # TRANSACTIONS
    # ----------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("transaction_ref", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("amount", sa.Integer, nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("org_id", sa.Integer,
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                  nullable=True, index=True),
        sa.Column("stripe_payment_intent_id", sa.String(128), nullable=True, index=True),
        sa.Column("stripe_checkout_session_id", sa.String(128), nullable=True, index=True),
        sa.Column("stripe_customer_id", sa.String(128), nullable=True, index=True),
        sa.Column("payment_link_url", sa.String(512), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("customer_phone", sa.String(32), nullable=True),
        sa.Column("razorpay_order_id", sa.String(128), nullable=True, index=True),
        sa.Column("razorpay_payment_id", sa.String(128), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ----------------------------------------------------------
    # FAILURE EVENTS
    # ----------------------------------------------------------
    op.create_table(
        "failure_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("transaction_id", sa.Integer,
                  sa.ForeignKey("transactions.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("gateway", sa.String(32), nullable=True),
        sa.Column("reason", sa.String(128), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # RECOVERY ATTEMPTS
    # ----------------------------------------------------------
    op.create_table(
        "recovery_attempts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("transaction_id", sa.Integer,
                  sa.ForeignKey("transactions.id", ondelete="CASCADE"),
                  nullable=True, index=True),
        sa.Column("transaction_ref", sa.String(64), nullable=True, index=True),
        sa.Column("channel", sa.String(16), nullable=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="created"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
    )

    # ----------------------------------------------------------
    # NOTIFICATION LOGS
    # ----------------------------------------------------------
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("recovery_attempt_id", sa.Integer,
                  sa.ForeignKey("recovery_attempts.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(32), nullable=True),
        sa.Column("provider_message_id", sa.String(128), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # RETRY POLICIES
    # ----------------------------------------------------------
    op.create_table(
        "retry_policies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer,
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("initial_delay_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("backoff_multiplier", sa.Integer, nullable=False, server_default="2"),
        sa.Column("max_delay_minutes", sa.Integer, nullable=False, server_default="1440"),
        sa.Column("enabled_channels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ----------------------------------------------------------
    # RECON LOGS
    # ----------------------------------------------------------
    op.create_table(
        "recon_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("transaction_id", sa.Integer,
                  sa.ForeignKey("transactions.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("stripe_checkout_session_id", sa.String(128), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(128), nullable=True),
        sa.Column("internal_status", sa.String(32), nullable=False),
        sa.Column("external_status", sa.String(32), nullable=True),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # PSP EVENTS
    # ----------------------------------------------------------
    op.create_table(
        "psp_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("psp_event_id", sa.String(160), nullable=False, unique=True, index=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # EMAIL OTP (HASHED)
    # ----------------------------------------------------------
    op.create_table(
        "email_otps",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("otp_hash", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False, server_default="email"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="5"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # MOBILE OTP
    # ----------------------------------------------------------
    op.create_table(
        "mobile_otps",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("mobile_number", sa.String(20), nullable=False, index=True),
        sa.Column("otp_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="5"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # OTP SECURITY LOGS
    # ----------------------------------------------------------
    op.create_table(
        "otp_security_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # ----------------------------------------------------------
    # USER SESSIONS
    # ----------------------------------------------------------
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("session_token", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("device_info", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )



def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("otp_security_logs")
    op.drop_table("mobile_otps")
    op.drop_table("email_otps")
    op.drop_table("psp_events")
    op.drop_table("recon_logs")
    op.drop_table("retry_policies")
    op.drop_table("notification_logs")
    op.drop_table("recovery_attempts")
    op.drop_table("failure_events")
    op.drop_table("api_keys")
    op.drop_table("transactions")
    op.drop_table("users")
    op.drop_table("organizations")
