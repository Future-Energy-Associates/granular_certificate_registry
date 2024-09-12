import datetime

from sqlmodel import Session

from gc_registry.database import db
from gc_registry.issuance_data.elexon.elexon import ElexonClient

engine = db.db_name_to_client["write"].engine


def seed_data():
    print("Seeding the database with data....")
    with Session(engine) as session:
        # Use PJM class to get data from the PJM API
        client = ElexonClient()
        from_date = datetime.datetime(2021, 1, 1, 0, 0, 0)
        to_date = from_date + datetime.timedelta(days=1)
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
        dataset = "B1610"
        data = client.get_dataset_in_datetime_range(
            dataset, from_date, to_date, bmu_ids=bmu_ids
        )
        certificate_bundles = client.map_generation_to_certificates(data)

        for certificate_bundle in certificate_bundles:
            session.add(certificate_bundle)
            session.commit()
            session.refresh(certificate_bundle)

    print("Seeding complete!")
