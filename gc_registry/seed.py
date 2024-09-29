import datetime

from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.core.database import cqrs, db
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.models import Device
from gc_registry.user.models import User


def seed_data():
    write_session = next(db.db_name_to_client["db_write"].yield_session())
    read_session = next(db.db_name_to_client["db_read"].yield_session())

    print("Seeding the database with data....")
    bmu_ids = [
        "E_MARK-1",
        "E_MARK-2",
        "RATS-1",
        "RATS-2",
        "RATS-3",
        "RATS-4",
        "RATSGT-2",
        "RATSGT-4",
    ]
    client = ElexonClient()
    from_date = datetime.datetime(2024, 1, 1, 0, 0, 0)
    to_date = from_date + datetime.timedelta(days=1)
    dataset = "B1610"

    # Create a User to add the certificates to
    user_dict = {
        "primary_contact": "a_user@usermail.com",
        "name": "A User",
        "roles": ["Production User"],
    }
    user = User.model_validate(user_dict)
    cqrs.write_to_database(user, write_session, read_session)
    read_session.refresh(user)

    # Create an Account to add the certificates to
    account_dict = {
        "account_name": "Test Account",
        "users": [user],
    }
    account = Account.model_validate(account_dict)
    cqrs.write_to_database(account, write_session, read_session)
    read_session.refresh(account)

    for bmu_id in bmu_ids:
        device_dict = {
            "device_name": bmu_id,
            "grid": "National Grid",
            "energy_source": "wind",
            "technology_type": "wind",
            "operational_date": datetime.datetime(2015, 1, 1, 0, 0, 0),
            "capacity": 1000,
            "peak_demand": 100,
            "location": "Some Location",
            "account_id": account.id,
        }
        device = Device.model_validate(device_dict)
        cqrs.write_to_database(device, write_session, read_session)
        read_session.refresh(device)

        # Use Elexon to get data from the Elexon API

        data_hh = client.get_dataset_in_datetime_range(
            dataset, from_date, to_date, bmu_ids=[bmu_id]
        )
        if data_hh.empty:
            print(f"No data found for {bmu_id}")
            continue
        data_hourly = client.resample_hh_data_to_hourly(data_hh)
        certificate_bundles = client.map_generation_to_certificates(
            data_hourly, account_id=account.id, device_id=device.id
        )

        cqrs.write_to_database(certificate_bundles, write_session, read_session)

    print("Seeding complete!")

    write_session.close()
    read_session.close()

    return
