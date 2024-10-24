"""Renamed table in SQLModel

Revision ID: 6409ce42f7e7
Revises: 2cb0ec2de122
Create Date: 2024-10-13 18:46:21.397515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '6409ce42f7e7'
down_revision: Union[str, None] = '2cb0ec2de122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Create the enum types
    energy_carrier_enum = sa.Enum('electricity', 'natural_gas', 'hydrogen', 'heat', 'other', name='energycarriertype')
    energy_carrier_enum.create(op.get_bind(), checkfirst=True)

    energy_source_enum = sa.Enum('solar_pv', 'wind', 'hydro', 'biomass', 'nuclear', 'electrolysis', 'geothermal', 'battery_storage', 'chp', 'other', name='energysourcetype')
    energy_source_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('registry_user',
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('primary_contact', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('roles', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_ids', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('organisation', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('storageaction_user_id_fkey', 'storageaction', type_='foreignkey')
    op.drop_constraint('useraccountlink_user_id_fkey', 'useraccountlink', type_='foreignkey')
    op.drop_table('user')
    op.add_column('granularcertificateaction', sa.Column('action_request_datetime_local', sa.DateTime(), nullable=True))
    op.add_column('granularcertificateaction', sa.Column('action_complete_datetime_local', sa.DateTime(), nullable=True))
    op.add_column('granularcertificatebundle', sa.Column('hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('granularcertificatebundle', sa.Column('id', sa.Integer(), nullable=False))
    op.alter_column('granularcertificatebundle', 'issuance_id',
               existing_type=sa.UUID(),
               type_=sqlmodel.sql.sqltypes.AutoString(),
               existing_nullable=False)
    op.alter_column('granularcertificatebundle', 'energy_carrier',
               existing_type=sa.VARCHAR(),
               type_=energy_carrier_enum,
               existing_nullable=False,
               postgresql_using="energy_carrier::energycarriertype")
    op.alter_column('granularcertificatebundle', 'energy_source',
               existing_type=sa.VARCHAR(),
               type_=energy_source_enum,
               existing_nullable=False,
               postgresql_using="energy_source::energysourcetype")
    op.create_foreign_key(None, 'storageaction', 'registry_user', ['user_id'], ['id'])
    op.create_foreign_key(None, 'useraccountlink', 'registry_user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'useraccountlink', type_='foreignkey')
    op.create_foreign_key('useraccountlink_user_id_fkey', 'useraccountlink', 'user', ['user_id'], ['id'])
    op.drop_constraint(None, 'storageaction', type_='foreignkey')
    op.create_foreign_key('storageaction_user_id_fkey', 'storageaction', 'user', ['user_id'], ['id'])
    op.alter_column('granularcertificatebundle', 'energy_source',
               existing_type=sa.Enum('solar_pv', 'wind', 'hydro', 'biomass', 'nuclear', 'electrolysis', 'geothermal', 'battery_storage', 'chp', 'other', name='energysourcetype'),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using="energy_source::VARCHAR")
    op.alter_column('granularcertificatebundle', 'energy_carrier',
               existing_type=sa.Enum('electricity', 'natural_gas', 'hydrogen', 'heat', 'other', name='energycarriertype'),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               postgresql_using="energy_carrier::VARCHAR")
    op.alter_column('granularcertificatebundle', 'certificate_status',
               existing_type=sa.VARCHAR(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.drop_table('registry_user')
    op.drop_column('granularcertificateaction', 'action_request_datetime_local')
    op.drop_column('granularcertificateaction', 'action_complete_datetime_local')
    op.drop_column('granularcertificatebundle', 'hash')
    op.drop_column('granularcertificatebundle', 'id')

    # Drop the enum types
    energy_carrier_enum = sa.Enum('electricity', 'natural_gas', 'hydrogen', 'heat', 'other', name='energycarriertype')
    energy_carrier_enum.drop(op.get_bind(), checkfirst=True)

    energy_source_enum = sa.Enum('solar_pv', 'wind', 'hydro', 'biomass', 'nuclear', 'electrolysis', 'geothermal', 'battery_storage', 'chp', 'other', name='energysourcetype')
    energy_source_enum.drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###