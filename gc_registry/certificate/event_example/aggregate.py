import datetime
from eventsourcing.domain import Aggregate, event


class GranularCertificateBundle(Aggregate):
    @event("Issue")
    def __init__(
        self,
        device_id: int,
        account_id: int,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
        certificate_status: str,
        face_value: float,
    ):
        self.device_id = device_id
        self.account_id = account_id
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.certificate_status = certificate_status
        self.face_value = face_value

    @event("Transfer")
    def transfer(self, account_id):
        self.account_id = account_id

    @event("Cancel")
    def cancel(self):
        self.certificate_status = "cancelled"
