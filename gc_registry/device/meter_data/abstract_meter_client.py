from abc import ABC, abstractmethod


class AbstractMeterDataClient(ABC):
    @abstractmethod
    def get_generation_by_device_in_datetime_range(self, *args, **kwargs):
        pass

    @abstractmethod
    def map_generation_to_certificates(self, *args, **kwargs):
        pass
