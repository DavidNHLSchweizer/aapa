
from abc import ABC, abstractmethod
from data.classes import AanvraagInfo
from data.storage import AAPStorage


class AanvraagStateProcessor(ABC):
    def __init__(self, storage: AAPStorage):
        self.storage = storage
        self._aanvraag: AanvraagInfo = None
    @property
    def aanvraag(self)->AanvraagInfo:
        return self._aanvraag
    @aanvraag.setter
    def aanvraag(self, value: AanvraagInfo):
        self._aanvraag = value
    @staticmethod
    def retrieve(storage: AAPStorage, id: int)->AanvraagInfo:
        return storage.aanvragen.read(id)
    def store(self): 
        self.storage.aanvragen.update(self.aanvraag)
    @abstractmethod
    def process(self, **kwargs):
        pass


