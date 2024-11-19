import datetime

import pandas as pd

from gc_registry.account.models import Account
from gc_registry.certificate.models import IssuanceMetaData
from gc_registry.core.database import cqrs, db, events
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
            device=device,
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
