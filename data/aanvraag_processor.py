from data.aanvraag_info import AanvraagInfo, FileType
from data.storage import AAPStorage

class AanvraagProcessor:
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        self.storage = storage
        self.aanvragen = aanvragen if aanvragen else storage.read_aanvragen()
        self.source_dict = self.__init_source_dict()
        self.__sort_aanvragen() 
    def __init_source_dict(self):
        result = {}
        for aanvraag in self.aanvragen:
            if file:=self.storage.find_fileinfo(aanvraag.id, FileType.AANVRAAG_PDF):
                result[aanvraag.id] = file
        return result
    def __sort_aanvragen(self):
        def get_timestamp(id):
            if fileinfo := self.source_dict.get(id, None):
                return fileinfo.timestamp
            else:
                return 0
        self.aanvragen.sort(key=lambda a: get_timestamp(a.id), reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)

