from abc import ABC, abstractmethod


class MeterDataClient(ABC):
    @abstractmethod
    def get_generation_by_device_in_datetime_range(*args, **kwargs):
        pass

    @abstractmethod
    def map_generation_to_certificates(*args, **kwargs):
        pass
