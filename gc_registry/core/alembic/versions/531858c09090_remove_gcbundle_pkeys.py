"""empty message

Revision ID: 531858c09090
Revises: 15a1762a0da6, 9b6ad74b1a31
Create Date: 2024-10-28 14:27:22.035326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '531858c09090'
down_revision: Union[str, None] = ('15a1762a0da6', '9b6ad74b1a31')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing primary key constraint
    op.drop_constraint('granularcertificatebundle_pkey', 'granularcertificatebundle', type_='primary')

    # Create a sequence for the id column
    op.execute("CREATE SEQUENCE granularcertificatebundle_id_seq")

    # Alter the id column to use the sequence and set it as the primary key
    op.execute("""
        ALTER TABLE granularcertificatebundle
        ALTER COLUMN id SET DEFAULT nextval('granularcertificatebundle_id_seq'),
        ALTER COLUMN id SET NOT NULL
    """)
    op.create_primary_key('granularcertificatebundle_pkey', 'granularcertificatebundle', ['id'])


def downgrade() -> None:
    # Drop the primary key constraint
    op.drop_constraint('granularcertificatebundle_pkey', 'granularcertificatebundle', type_='primary')

    # Remove the default value and sequence from the id column
    op.execute("""
        ALTER TABLE granularcertificatebundle
        ALTER COLUMN id DROP DEFAULT,
        ALTER COLUMN id DROP NOT NULL
    """)

    # Drop the sequence
    op.execute("DROP SEQUENCE granularcertificatebundle_id_seq")

    # Recreate the primary key constraint
    op.create_primary_key('granularcertificatebundle_pkey', 'granularcertificatebundle', ['id'])