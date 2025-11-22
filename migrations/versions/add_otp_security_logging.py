"""Add OTP security logging

Revision ID: otp_security_001
Revises: enhanced_auth_001
Create Date: 2024-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'otp_security_001'
down_revision = 'enhanced_auth_001'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # ### Create OTP Security Log table ###
    op.create_table('otp_security_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('blocked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_otp_security_logs_id'), 'otp_security_logs', ['id'], unique=False)
    op.create_index(op.f('ix_otp_security_logs_email'), 'otp_security_logs', ['email'], unique=False)
    op.create_index('ix_otp_security_logs_email_action', 'otp_security_logs', ['email', 'action'], unique=False)
    op.create_index('ix_otp_security_logs_created_at', 'otp_security_logs', ['created_at'], unique=False)
    op.create_index('ix_otp_security_logs_blocked_until', 'otp_security_logs', ['blocked_until'], unique=False)


def downgrade():
    # ### Remove OTP Security Log table ###
    op.drop_index('ix_otp_security_logs_blocked_until', table_name='otp_security_logs')
    op.drop_index('ix_otp_security_logs_created_at', table_name='otp_security_logs')
    op.drop_index('ix_otp_security_logs_email_action', table_name='otp_security_logs')
    op.drop_index(op.f('ix_otp_security_logs_email'), table_name='otp_security_logs')
    op.drop_index(op.f('ix_otp_security_logs_id'), table_name='otp_security_logs')
    op.drop_table('otp_security_logs')