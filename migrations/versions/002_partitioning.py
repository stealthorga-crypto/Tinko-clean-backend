"""monthly partitioning stubs

Revision ID: 002_partitioning
Revises: 001_initial_schema
Create Date: 2025-10-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_partitioning'
down_revision: Union[str, Sequence[str], None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create helper function to ensure current month partitions (Postgres only)."""
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION ensure_current_month_partitions()
            RETURNS void AS $$
            DECLARE
                ymon text := to_char(now(), 'YYYYMM');
            BEGIN
                -- Placeholder: In a full implementation, we'd create partitions for failure_events and recovery_attempts
                RAISE NOTICE 'Ensuring partitions for %', ymon;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    op.execute(sa.text("DROP FUNCTION IF EXISTS ensure_current_month_partitions();"))
