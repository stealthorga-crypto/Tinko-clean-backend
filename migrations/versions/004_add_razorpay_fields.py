"""add razorpay fields to transaction

Revision ID: 004_add_razorpay_fields
Revises: 003_user_role_operator
Create Date: 2025-10-23 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_add_razorpay_fields'
down_revision: Union[str, Sequence[str], None] = '003_user_role_operator'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.add_column(sa.Column('razorpay_order_id', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('razorpay_payment_id', sa.String(length=128), nullable=True))
        batch_op.create_index('ix_transactions_razorpay_order_id', 'razorpay_order_id')
        batch_op.create_index('ix_transactions_razorpay_payment_id', 'razorpay_payment_id')


def downgrade() -> None:
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_index('ix_transactions_razorpay_payment_id')
        batch_op.drop_index('ix_transactions_razorpay_order_id')
        batch_op.drop_column('razorpay_payment_id')
        batch_op.drop_column('razorpay_order_id')
