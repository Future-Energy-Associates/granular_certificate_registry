import datetime
from typing import Any

import pandas as pd
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.core.database import db
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.models import Device
from gc_registry.user.models import User


def get_device_capacities(bmu_ids: list[str]) -> list[dict[str, Any]]:

    client = ElexonClient()
    dataset = "IGCPU"
    to_datetime = datetime.datetime.now().date()
    from_datetime = to_datetime - datetime.timedelta(days=2 * 365)

    data = client.get_asset_dataset_in_datetime_range(
        dataset, from_datetime, to_datetime
    )

    df = pd.DataFrame(data["data"])

    df.sort_values("effectiveFrom", inplace=True, ascending=True)
    df.drop_duplicates(subset=["registeredResourceName"], inplace=True, keep="last")
    df = df[df.bmUnit.notna()]
    df = df[df.bmUnit.str.contains("|".join(bmu_ids))]
    df = df[["bmUnit", "installedCapacity"]]
    df["installedCapacity"] = df["installedCapacity"].astype(int)

    df.to_csv("device_capacities.csv", index=False)

    # check if all bmu_ids are in the data
    if len(df) != len(bmu_ids):
        missing_bmu_ids = set(bmu_ids) - set(df["bmUnit"])
        raise ValueError(f"Missing BMU IDs: {missing_bmu_ids}")

    device_dictionary = df.to_dict(orient="records")
    device_capacities = {
        device["bmUnit"]: device["installedCapacity"] for device in device_dictionary
    }

    return device_capacities


def seed_data():
    client = db.db_name_to_client["write"]
    engine = client.engine

    print("Seeding the database with data....")
    bmu_ids = [
        "E_MARK-1",
        "T_RATS-1",
        "T_RATS-2",
        "T_RATS-3",
        "T_RATS-4",
        "T_RATSGT-2",
        "T_RATSGT-4",
    ]

    device_capacities = get_device_capacities(bmu_ids)

    client = ElexonClient()
    from_date = datetime.datetime(2024, 1, 1, 0, 0, 0)
    to_date = from_date + datetime.timedelta(days=1)
    dataset = "B1610"

    with Session(engine) as session:
        # Create a User to add the certificates to
        user_dict = {
            "primary_contact": "a_user@usermail.com",
            "name": "A User",
            "role": ["Production User"],
            "created_at": datetime.datetime.utcnow(),
        }
        user = User.model_validate(user_dict)

        session.add(user)
        session.commit()
        session.refresh(user)

        # Create an Account to add the certificates to
        account_dict = {
            "account_name": "Test Account",
            "users": [user],
            "created_at": datetime.datetime.utcnow(),
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
                "capacity": device_capacities[bmu_id],
                "peak_demand": 100,
                "location": "Some Location",
                "account_id": account.id,
                "created_at": datetime.datetime.utcnow(),
                "is_storage": False,
            }
            device = Device.model_validate(device_dict)
            session.add(device)
            session.commit()
            session.refresh(device)

            # Use Elexon to get data from the Elexon API

            data = client.get_sp_dataset_in_datetime_range(
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
