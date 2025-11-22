"""
Monthly partitions for transactions (Postgres only, no-op on SQLite).

Revision ID: 005_partitions
Revises: 004_add_razorpay_fields
Create Date: 2025-10-23
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta, timezone


# revision identifiers, used by Alembic.
revision = '005_partitions'
down_revision = '004_add_razorpay_fields'
branch_labels = None
depends_on = None


def _month_bounds(dt: datetime) -> tuple[datetime, datetime]:
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect != 'postgresql':
        # No-op on SQLite and others
        return

    now = datetime.now(timezone.utc)
    months = [now, (now.replace(day=28) + timedelta(days=4))]  # next month via overflow trick

    for m in months:
        start, end = _month_bounds(m)
        suffix = f"y{start.year}m{start.month:02d}"
        part_table = f"transactions_{suffix}"
        # Create partition table and attach; wrap in DO block to ignore if parent not partitioned
        sql = f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = '{part_table}' AND n.nspname = 'public'
            ) THEN
                EXECUTE 'CREATE TABLE public.{part_table} (LIKE public.transactions INCLUDING ALL)';
            END IF;
            BEGIN
                EXECUTE 'ALTER TABLE public.transactions ATTACH PARTITION public.{part_table} FOR VALUES FROM (\"{start.isoformat()}\") TO (\"{end.isoformat()}\")';
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'Partition attach skipped for {part_table} (parent may not be partitioned)';
            END;
        END $$;
        """
        conn.execute(sa.text(sql))


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect != 'postgresql':
        return
    # Safe no-op: keep historical partitions
    pass
