"""test_migration

Revision ID: 15a1762a0da6
Revises: 6409ce42f7e7
Create Date: 2024-10-15 17:25:59.652064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '15a1762a0da6'
down_revision: Union[str, None] = '6409ce42f7e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('granularcertificatebundle', sa.Column('is_deleted', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('granularcertificatebundle', 'is_deleted')
    # ### end Alembic commands ###