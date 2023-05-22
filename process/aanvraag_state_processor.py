
from data.classes import AanvraagInfo
from data.storage import AAPStorage


class AanvraagStateProcessor:
    def __init__(self, storage: AAPStorage):
        self.storage = storage
        self._aanvraag: AanvraagInfo = None
    @property
    def aanvraag(self)->AanvraagInfo:
        return self._aanvraag
    @aanvraag.setter
    def aanvraag(self, value: AanvraagInfo):
        self._aanvraag = self.retrieve(value.id)
    def retrieve(self, id: int)->AanvraagInfo:
        return self.storage.read_aanvraag(id)
    def store(self): 
        self.storage.update_aanvraag(self.aanvraag)