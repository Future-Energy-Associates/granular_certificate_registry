"""adding_storage

Revision ID: 1832fcb8a0de
Revises: 61e06ddd23e6
Create Date: 2024-09-22 13:01:32.734755

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1832fcb8a0de"
down_revision: Union[str, None] = "61e06ddd23e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "storagechargerecord",
        sa.Column("charging_start_datetime", sa.DateTime(), nullable=False),
        sa.Column("charging_end_datetime", sa.DateTime(), nullable=False),
        sa.Column("charging_energy", sa.Integer(), nullable=False),
        sa.Column("charging_energy_source", sa.String(), nullable=False),
        sa.Column("gc_issuance_id", sa.Integer(), nullable=False),
        sa.Column("certificate_bundle_id_range_start", sa.Integer(), nullable=False),
        sa.Column("certificate_bundle_id_range_end", sa.Integer(), nullable=False),
        sa.Column("scr_geographic_matching_method", sa.String(), nullable=False),
        sa.Column("sdr_allocation_id", sa.Integer(), nullable=True),
        sa.Column("scr_allocation_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("scr_allocation_id"),
    )
    op.create_table(
        "storagedischargerecord",
        sa.Column("discharging_start_datetime", sa.DateTime(), nullable=False),
        sa.Column("discharging_end_datetime", sa.DateTime(), nullable=False),
        sa.Column("discharge_energy", sa.Float(), nullable=False),
        sa.Column("charging_energy_source", sa.String(), nullable=False),
        sa.Column("scr_allocation_methodology", sa.String(), nullable=False),
        sa.Column("efficiency_factor_methodology", sa.String(), nullable=False),
        sa.Column("efficiency_factor_interval_start", sa.DateTime(), nullable=True),
        sa.Column("efficiency_factor_interval_end", sa.DateTime(), nullable=True),
        sa.Column("sdr_allocation_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("scr_allocation_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scr_allocation_id"],
            ["storagechargerecord.scr_allocation_id"],
        ),
        sa.PrimaryKeyConstraint("sdr_allocation_id"),
    )
    op.create_foreign_key(
        "granularcertificatebundle_sdr_allocation_id_fkey",
        "granularcertificatebundle",
        "storagedischargerecord",
        ["sdr_allocation_id"],
        ["sdr_allocation_id"],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "granularcertificatebundle_sdr_allocation_id_fkey",
        "granularcertificatebundle",
        type_="foreignkey",
    )
    op.drop_table("storagedischargerecord")
    op.drop_table("storagechargerecord")
    # ### end Alembic commands ###
