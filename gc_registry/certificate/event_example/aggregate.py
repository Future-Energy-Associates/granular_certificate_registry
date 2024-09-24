import datetime
from eventsourcing.domain import Aggregate, event

from gc_registry.certificate.schemas import GranularCertificateBundleBase


class GranularCertificateBundle(Aggregate, GranularCertificateBundleBase):
    @event("Issue")
    def __init__(
        self,
        device_id: int,
        account_id: int,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.device_id = device_id
        self.account_id = account_id

    @event("Transfer")
    def transfer(self, account_id):
        self.account_id = account_id

    @event("Cancel")
    def cancel(self):
        self.certificate_status = "cancelled"
