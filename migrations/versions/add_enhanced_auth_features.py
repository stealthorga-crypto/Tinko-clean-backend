"""Add enhanced authentication features

Revision ID: enhanced_auth_001
Revises: (previous_revision)
Create Date: 2024-11-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhanced_auth_001'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # ### Enhanced User table ###
    
    # Add new columns to users table
    op.add_column('users', sa.Column('auth_providers', sa.JSON(), nullable=False, server_default='["email"]'))
    op.add_column('users', sa.Column('google_id', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('account_type', sa.String(length=32), nullable=False, server_default='user'))
    
    # Make hashed_password nullable for OAuth-only users
    op.alter_column('users', 'hashed_password', nullable=True)
    
    # Add indexes
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=False)
    
    # ### Create API Keys table ###
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_name', sa.String(length=128), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False, server_default='["read"]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)


def downgrade():
    # ### Remove API Keys table ###
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_table('api_keys')
    
    # ### Revert User table changes ###
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    
    op.drop_column('users', 'account_type')
    op.drop_column('users', 'is_email_verified')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'auth_providers')
    
    # Revert hashed_password to not nullable
    op.alter_column('users', 'hashed_password', nullable=False)