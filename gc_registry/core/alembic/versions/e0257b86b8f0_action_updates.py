"""action_updates

Revision ID: e0257b86b8f0
Revises: 4e7cd9131146
Create Date: 2024-11-27 18:04:33.909901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0257b86b8f0'
down_revision: str | None = '9c5b09eea511'
branch_labels: str | Sequence[str] | None = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('granularcertificateaction', sa.Column('granular_certificate_bundle_ids', sa.JSON(), nullable=True))
    # op.add_column('granularcertificateaction', sa.Column('certificate_quantity', sa.Integer(), nullable=True))
    # op.add_column('granularcertificateaction', sa.Column('certificate_bundle_percentage', sa.Float(), nullable=True))
    # op.add_column('granularcertificateaction', sa.Column('certificate_status', sa.Enum('ACTIVE', 'CANCELLED', 'CLAIMED', 'EXPIRED', 'WITHDRAWN', 'LOCKED', 'RESERVED', name='certificatestatus'), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_column('granularcertificateaction', 'certificate_status')
    # op.drop_column('granularcertificateaction', 'certificate_bundle_percentage')
    # op.drop_column('granularcertificateaction', 'certificate_quantity')
    op.drop_column('granularcertificateaction', 'granular_certificate_bundle_ids')
    # ### end Alembic commands ###