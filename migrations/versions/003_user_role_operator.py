"""set default user role to operator and migrate existing

Revision ID: 003_user_role_operator
Revises: 002_partitioning
Create Date: 2025-10-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_user_role_operator'
down_revision: Union[str, Sequence[str], None] = '002_partitioning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    # Update default for users.role to 'operator'
    if dialect == 'postgresql':
        op.alter_column('users', 'role', server_default=sa.text("'operator'"))
    else:
        try:
            op.alter_column('users', 'role', server_default='operator')
        except Exception:
            pass
    # Migrate existing 'user' -> 'operator'
    op.execute("UPDATE users SET role='operator' WHERE role='user'")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    # Revert default to 'user'
    if dialect == 'postgresql':
        op.alter_column('users', 'role', server_default=sa.text("'user'"))
    else:
        try:
            op.alter_column('users', 'role', server_default='user')
        except Exception:
            pass
