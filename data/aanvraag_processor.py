from data.aanvraag_info import AanvraagInfo
from data.storage import AAPStorage

class AanvraagProcessor:
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        self.storage = storage
        self.aanvragen = aanvragen if aanvragen else sorted(storage.read_aanvragen(), key=lambda a: a.fileinfo.timestamp, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)

