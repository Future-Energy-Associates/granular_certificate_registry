import datetime
from eventsourcing.domain import Aggregate, event

from gc_registry.certificate.schemas import (
    GranularCertificateBundleBase,
)


class GranularCertificateBundleAggregate(Aggregate, GranularCertificateBundleBase):
    @event("Issue")
    def __init__(
        self,
        device_id: int,
        account_id: int,
        certificate_status: str,
        bundle_id_range_start: int,
        bundle_id_range_end: int,
        bundle_quantity: int,
        energy_carrier: str,
        energy_source: str,
        face_value: int,
        issuance_post_energy_carrier_conversion: bool,
        production_starting_interval: datetime.datetime,
        production_ending_interval: datetime.datetime,
        issuance_datestamp: datetime.datetime,
        expiry_datestamp: datetime.datetime,
        is_storage: bool,
        sdr_allocation_id: int | None = None,
        storage_efficiency_factor: float | None = None,
        registry_id: int = 1,
    ):
        super().__init__()
        self.device_id = device_id
        self.account_id = account_id
        self.certificate_status = certificate_status
        self.bundle_id_range_start = bundle_id_range_start
        self.bundle_id_range_end = bundle_id_range_end
        self.bundle_quantity = bundle_quantity
        self.energy_carrier = energy_carrier
        self.energy_source = energy_source
        self.face_value = face_value
        self.issuance_post_energy_carrier_conversion = (
            issuance_post_energy_carrier_conversion
        )
        self.production_starting_interval = production_starting_interval
        self.production_ending_interval = production_ending_interval
        self.issuance_datestamp = issuance_datestamp
        self.expiry_datestamp = expiry_datestamp
        self.is_storage = is_storage
        self.sdr_allocation_id = sdr_allocation_id
        self.storage_efficiency_factor = storage_efficiency_factor

    @event("Transfer")
    def transfer(self, account_id):
        self.account_id = account_id

    @event("Cancel")
    def cancel(self):
        self.certificate_status = "cancelled"


if __name__ == "__main__":
    print(dir(GranularCertificateBundleBase))
    print([f"{k}" for k in GranularCertificateBundleBase.__dict__.keys()])
