from sqlmodel import Session

from src.datamodel import db
from src.issuance_data.pjm.pjm import PJM

engine = db.db_name_to_client["write"].engine


def seed_data():
    print("Seeding the database with data....")
    with Session(engine) as session:
        # Use PJM class to get data from the PJM API
        pjm = PJM()
        response = pjm.get_data("gen_by_fuel", test=True)
        certificate_bundles = pjm.map_generation_to_certificates(response.json())

        for certificate_bundle in certificate_bundles:
            session.add(certificate_bundle)
            session.commit()
            session.refresh(certificate_bundle)

    print("Seeding complete!")
