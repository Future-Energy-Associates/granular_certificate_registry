import datetime
import os
from dotenv import load_dotenv
from eventsourcing.application import Application
from gc_registry.certificate.event_example.aggregate import GranularCertificateBundle

load_dotenv()


os.environ["PERSISTENCE_MODULE"] = "eventsourcing.postgres"
os.environ["POSTGRES_DBNAME"] = os.environ["POSTGRES_DB"]
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5436"


class Registry(Application):
    def issue_certificate(
        self,
        device_id: int,
        account_id: int,
        **kwargs,
    ):
        gcb = GranularCertificateBundle(
            device_id,
            account_id,
            **kwargs,
        )
        self.save(gcb)
        return gcb.id

    def transfer(self, id, account_id):
        gcb = self.repository.get(id)
        gcb.transfer(account_id)
        self.save(gcb)

    def cancel(self, issuance_id):
        gcb = self.repository.get(issuance_id)
        gcb.cancel()
        self.save(gcb)

    def get_granular_certificate_bundle(self, issuance_id):
        gcb = self.repository.get(issuance_id)
        return gcb.__dict__
