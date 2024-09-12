import datetime
from sqlalchemy import select
from sqlmodel import Session

from src.datamodel import db
from src.issuance_data.pjm.pjm import PJM
from src.issuance_data.elexon.elexon import ElexonClient
from src.datamodel.schemas.entities import Account, Device

engine = db.db_name_to_client["write"].engine


def seed_data():
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

        # Create an Account to add the certificates to
        account_dict = {
            "account_name": "Test Account",
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
                "account_id": account.account_id,
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
                data, account_id=account.account_id, device_id=device.device_id
            )

            for certificate_bundle in certificate_bundles:
                session.add(certificate_bundle)
                session.commit()
                # session.refresh(certificate_bundle)

    print("Seeding complete!")
