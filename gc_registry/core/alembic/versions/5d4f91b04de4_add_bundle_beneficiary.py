"""add_bundle_beneficiary

Revision ID: 5d4f91b04de4
Revises: f1fe59b637f7
Create Date: 2024-11-27 18:57:56.193512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5d4f91b04de4'
down_revision: Union[str, None] = 'f1fe59b637f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('granularcertificatebundle', sa.Column('beneficiary', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('granularcertificatebundle', 'beneficiary')
    # ### end Alembic commands ###