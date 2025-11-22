"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-18 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create all tables."""
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=True),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_org_id'), 'users', ['org_id'], unique=False)
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_ref', sa.String(length=64), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=8), nullable=True),
        sa.Column('org_id', sa.Integer(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=128), nullable=True),
        sa.Column('stripe_checkout_session_id', sa.String(length=128), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=128), nullable=True),
        sa.Column('payment_link_url', sa.String(length=512), nullable=True),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_ref')
    )
    op.create_index(op.f('ix_transactions_transaction_ref'), 'transactions', ['transaction_ref'], unique=True)
    op.create_index(op.f('ix_transactions_org_id'), 'transactions', ['org_id'], unique=False)
    op.create_index(op.f('ix_transactions_stripe_payment_intent_id'), 'transactions', ['stripe_payment_intent_id'], unique=False)
    op.create_index(op.f('ix_transactions_stripe_checkout_session_id'), 'transactions', ['stripe_checkout_session_id'], unique=False)
    op.create_index(op.f('ix_transactions_stripe_customer_id'), 'transactions', ['stripe_customer_id'], unique=False)
    
    # Create failure_events table
    op.create_table('failure_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('gateway', sa.String(length=32), nullable=True),
        sa.Column('reason', sa.String(length=128), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_failure_events_transaction_id'), 'failure_events', ['transaction_id'], unique=False)
    
    # Create recovery_attempts table
    op.create_table('recovery_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('transaction_ref', sa.String(length=64), nullable=True),
        sa.Column('channel', sa.String(length=16), nullable=True),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='created'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_recovery_attempts_transaction_id'), 'recovery_attempts', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_recovery_attempts_transaction_ref'), 'recovery_attempts', ['transaction_ref'], unique=False)
    op.create_index(op.f('ix_recovery_attempts_token'), 'recovery_attempts', ['token'], unique=True)
    
    # Create notification_logs table
    op.create_table('notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recovery_attempt_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=16), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='pending'),
        sa.Column('provider', sa.String(length=32), nullable=True),
        sa.Column('provider_message_id', sa.String(length=128), nullable=True),
        sa.Column('error_message', sa.String(length=512), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['recovery_attempt_id'], ['recovery_attempts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_recovery_attempt_id'), 'notification_logs', ['recovery_attempt_id'], unique=False)
    
    # Create retry_policies table
    op.create_table('retry_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('initial_delay_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('backoff_multiplier', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('max_delay_minutes', sa.Integer(), nullable=False, server_default='1440'),
        sa.Column('enabled_channels', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[\"email\"]'::json")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retry_policies_org_id'), 'retry_policies', ['org_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - drop all tables."""
    op.drop_index(op.f('ix_retry_policies_org_id'), table_name='retry_policies')
    op.drop_table('retry_policies')
    op.drop_index(op.f('ix_notification_logs_recovery_attempt_id'), table_name='notification_logs')
    op.drop_table('notification_logs')
    op.drop_index(op.f('ix_recovery_attempts_token'), table_name='recovery_attempts')
    op.drop_index(op.f('ix_recovery_attempts_transaction_ref'), table_name='recovery_attempts')
    op.drop_index(op.f('ix_recovery_attempts_transaction_id'), table_name='recovery_attempts')
    op.drop_table('recovery_attempts')
    op.drop_index(op.f('ix_failure_events_transaction_id'), table_name='failure_events')
    op.drop_table('failure_events')
    op.drop_index(op.f('ix_transactions_stripe_customer_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_stripe_checkout_session_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_stripe_payment_intent_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_org_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transaction_ref'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_users_org_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
