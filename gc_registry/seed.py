import datetime
from typing import Any

import pandas as pd

from gc_registry.account.models import Account
from gc_registry.certificate.models import IssuanceMetaData
from gc_registry.certificate.services import issue_certificates_in_date_range
from gc_registry.core.database import cqrs, db, events
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.models import Device
from gc_registry.user.models import User


def seed_data():
    _ = db.get_db_name_to_client()
    write_session = db.get_write_session()
    read_session = db.get_read_session()
    esdb_client = events.get_esdb_client()

    print("Seeding the WRITE database with data....")

    bmu_ids = [
        "E_MARK-1",
        "T_RATS-1",
        "T_RATS-2",
        "T_RATS-3",
        "T_RATS-4",
        "T_RATSGT-2",
        "T_RATSGT-4",
    ]

    client = ElexonClient()
    from_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
    to_datetime = from_datetime + datetime.timedelta(days=1)

    device_capacities = client.get_device_capacities(bmu_ids)

    # Create a User to add the certificates to
    user_dict = {
        "primary_contact": "a_user@usermail.com",
        "name": "A User",
        "roles": ["Production User"],
    }
    user = User.create(user_dict, write_session, read_session, esdb_client)[0]

    # Create an Account to add the certificates to
    account_dict = {
        "account_name": "Test Account",
        "user_ids": [user.id],
    }
    account = Account.create(account_dict, write_session, read_session, esdb_client)[0]

    # Create issuance metadata for the certificates
    issuance_metadata_dict = {
        "country_of_issuance": "UK",
        "connected_grid_identification": "NESO",
        "issuing_body": "OFGEM",
        "legal_status": "legal",
        "issuance_purpose": "compliance",
        "support_received": None,
        "quality_scheme_reference": None,
        "dissemination_level": None,
        "issue_market_zone": "NESO",
    }

    issuance_metadata = IssuanceMetaData.create(
        issuance_metadata_dict, write_session, read_session, esdb_client
    )[0]

    for bmu_id in bmu_ids:
        device_dict = {
            "device_name": bmu_id,
            "meter_data_id": bmu_id,
            "grid": "National Grid",
            "energy_source": "wind",
            "technology_type": "wind",
            "operational_date": str(datetime.datetime(2015, 1, 1, 0, 0, 0)),
            "capacity": device_capacities[bmu_id],
            "peak_demand": 100,
            "location": "Some Location",
            "account_id": account.id,
            "is_storage": False,
        }
        device = Device.create(device_dict, write_session, read_session, esdb_client)[0]

        # Use Elexon to get data from the Elexon API
        data_hh = client.get_metering_by_device_in_datetime_range(
            from_datetime, to_datetime, meter_data_id=bmu_id
        )
        if len(data_hh) == 0:
            print(f"No data found for {bmu_id}")
            continue
        data_hh_df = pd.DataFrame(data_hh)
        data_hourly_dict = client.resample_hh_data_to_hourly(data_hh_df)

        certificate_bundles = client.map_metering_to_certificates(
            data_hourly_dict,
            account_id=account.id,
            device_id=device.id,
            is_storage=False,
            issuance_metadata_id=issuance_metadata.id,
        )

        if not certificate_bundles:
            print(f"No certificate bundles found for {bmu_id}")
        else:
            _ = cqrs.write_to_database(
                certificate_bundles, write_session, read_session, esdb_client
            )

    print("Seeding complete!")

    write_session.close()
    read_session.close()

    return



def create_device_account_and_user(device_name,write_session, read_session, esdb_client):

    """ Create a default device, account and user for the device"""

    user_dict = {
        "primary_contact": "a_user@usermail.com",
        "name": f"Default user for {device_name}",
        "roles": ["Production User"],
    }
    user = User.create(user_dict, write_session, read_session, esdb_client)[0]


    account_dict = {
        "account_name": f"Default account for {device_name}",
        "user_ids": [user.id],
    }
    account = Account.create(account_dict, write_session, read_session, esdb_client)[0]

    return account, user


def seed_all_generators_from_elexon(from_date: datetime.date = datetime.date(2020,1,1)):
    """
    Seed the database with all generators data from the given source
    
    Args:
        client: The client to use to get the data
        from_datetime: The start datetime to get the data from
        to_datetime: The end datetime to get the data to
    """

    client = ElexonClient()

    _ = db.get_db_name_to_client()
    write_session = db.get_write_session()
    read_session = db.get_read_session()
    esdb_client = events.get_esdb_client()

    # Create year long ranges from the from_date to the to_date
    data_list: list[dict[str, Any]] = []
    now = datetime.datetime.now()
    for from_datetime in pd.date_range(from_date,now.date(),freq="Y"):
        year_period_end = from_datetime + datetime.timedelta(days=365)
        to_datetime = year_period_end if year_period_end < now else now

        print(f"Getting data from {from_datetime} to {to_datetime}")

        data = client.get_asset_dataset_in_datetime_range(
            dataset="IGCPU",
            from_date=from_datetime,
            to_date=to_datetime,
        )
        data_list.extend(data['data'])

    df = pd.DataFrame(data_list)

    df.sort_values("effectiveFrom", inplace=True, ascending=True)
    df.drop_duplicates(subset=["registeredResourceName"], inplace=True, keep="last")
    df = df[df.bmUnit.notna()]
    df["installedCapacity"] = df["installedCapacity"].astype(int)

    # drop all non-renewable psr types
    df = df[df.psrType.isin(client.renewable_psr_types)]

    WATTS_IN_MEGAWATT = 1e6

    for bmu_dict in df.to_dict(orient="records"):

        account, _ = create_device_account_and_user(bmu_dict["registeredResourceName"],write_session, read_session, esdb_client)

        device_dict = {
            "device_name": bmu_dict["registeredResourceName"],
            "meter_data_id": bmu_dict["bmUnit"],
            "grid": "National Grid",
            "energy_source": client.psr_type_to_energy_source.get(bmu_dict["psrType"], "other"),
            "technology_type": bmu_dict["psrType"],
            "operational_date": str(datetime.datetime(2015, 1, 1, 0, 0, 0)),
            "capacity": bmu_dict["installedCapacity"] * WATTS_IN_MEGAWATT,
            "location": "Some Location",
            "account_id": account.id,
            "is_storage": False,
            "peak_demand":-bmu_dict["installedCapacity"]*0.01,
        }
        _ = Device.create(device_dict, write_session, read_session, esdb_client)[0]

def seed_certificates_for_all_devices_in_date_range(from_date:datetime.date,to_date:datetime.date) -> None:
    """
    Seed the database with all generators data from the given source
    Args:
        client: The client to use to get the data
        from_datetime: The start datetime to get the data from
        to_datetime: The end datetime to get the data to
    """

    _ = db.get_db_name_to_client()
    write_session = db.get_write_session()
    read_session = db.get_read_session()
    esdb_client = events.get_esdb_client()

    client = ElexonClient()

    # Create issuance metadata for the certificates
    issuance_metadata_dict = {
        "country_of_issuance": "UK",
        "connected_grid_identification": "NESO",
        "issuing_body": "OFGEM",
        "legal_status": "legal",
        "issuance_purpose": "compliance",
        "support_received": None,
        "quality_scheme_reference": None,
        "dissemination_level": None,
        "issue_market_zone": "NESO",
    }

    issuance_metadata = IssuanceMetaData.create(
        issuance_metadata_dict, write_session, read_session, esdb_client
    )[0]

    issue_certificates_in_date_range(from_date,to_date,write_session,read_session,esdb_client,issuance_metadata.id,client)


if __name__ == "__main__":
    seed_all_generators_from_elexon()
    to_date = (datetime.datetime.now() - datetime.timedelta(days=7))
    from_date = to_date - datetime.timedelta(days=1)
    seed_certificates_for_all_devices_in_date_range(from_date,to_date)

