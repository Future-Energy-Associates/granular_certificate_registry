import datetime

from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.core.database import db
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.models import Device
from gc_registry.user.models import User


def seed_data():
    client = db.db_name_to_client["db_write"]
    engine = client.engine

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

    with Session(engine) as session:
        # Create a User to add the certificates to
        user_dict = {
            "primary_contact": "a_user@usermail.com",
            "name": "A User",
            "roles": ["Production User"],
        }
        user = User.model_validate(user_dict)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create an Account to add the certificates to
        account_dict = {
            "account_name": "Test Account",
            "users": [user],
        }
        account = Account.model_validate(account_dict)
        session.add(account)
        session.commit()
        session.refresh(account)

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
            session.add(device)
            session.commit()
            session.refresh(device)

            # Use Elexon to get data from the Elexon API

            data = client.get_dataset_in_datetime_range(
                dataset, from_date, to_date, bmu_ids=[bmu_id]
            )
            certificate_bundles = client.map_generation_to_certificates(
                data, account_id=account.id, device_id=device.id
            )

            for certificate_bundle in certificate_bundles:
                session.add(certificate_bundle)
                session.commit()
                session.refresh(certificate_bundle)

    print("Seeding complete!")
