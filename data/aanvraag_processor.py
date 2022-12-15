from data.aanvraag_info import AanvraagInfo, FileType
from data.storage import AAPStorage

class AanvraagProcessor:
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        self.storage = storage
        self.aanvragen = aanvragen if aanvragen else storage.read_aanvragen()
        self.__sort_aanvragen() 
    def __sort_aanvragen(self):
        self.aanvragen.sort(key=lambda a:a.timestamp, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)

