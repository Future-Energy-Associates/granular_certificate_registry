"""merge_multiple_heads

Revision ID: cd5332cc273e
Revises: 4e7cd9131146, e0257b86b8f0
Create Date: 2024-11-28 19:38:33.200584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd5332cc273e'
down_revision: Union[str, None] = ('4e7cd9131146', 'e0257b86b8f0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass