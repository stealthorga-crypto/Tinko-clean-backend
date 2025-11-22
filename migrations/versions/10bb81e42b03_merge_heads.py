"""merge heads

Revision ID: 10bb81e42b03
Revises: 005_partitions, otp_security_001
Create Date: 2025-11-15 17:50:40.560843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10bb81e42b03'
down_revision: Union[str, Sequence[str], None] = ('005_partitions', 'otp_security_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
