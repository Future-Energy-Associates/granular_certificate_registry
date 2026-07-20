"""add_export_action_enum

Revision ID: 7cdfaba8fa31
Revises: 2f7dda77c60f
Create Date: 2025-09-10 10:53:41.095428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7cdfaba8fa31'
down_revision: Union[str, None] = '2f7dda77c60f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE certificateactiontype ADD VALUE IF NOT EXISTS 'EXPORT'")
    op.execute("ALTER TYPE certificateactiontype ADD VALUE IF NOT EXISTS 'CANCEL_FOR_STORAGE'")
    op.execute("ALTER TYPE certificatestatus ADD VALUE IF NOT EXISTS 'EXPORTED'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # If you need to remove these values, you would need to:
    # 1. Create a new enum without these values
    # 2. Update all columns to use the new enum
    # 3. Drop the old enum
    # 4. Rename the new enum
    pass