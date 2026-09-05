"""merge multiple heads

Revision ID: a38ea5ee4ede
Revises: 89d71c452669, 92ce9976970c
Create Date: 2026-09-03 00:17:09.969906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a38ea5ee4ede'
down_revision: Union[str, Sequence[str], None] = ('89d71c452669', '92ce9976970c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
