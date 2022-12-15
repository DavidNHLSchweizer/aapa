from data.aanvraag_info import AanvraagInfo, FileType
from data.storage import AAPStorage
from general.log import logInfo

# def dumpaanvragen(aanvragen):
#     print('dumpi')
#     for aanvraag in aanvragen:
#         print(f'aanvraag: {aanvraag}   timestamp: {aanvraag.timestamp}  source: {aanvraag.files.get_info(FileType.AANVRAAG_PDF)}')
class AanvraagProcessor:
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        self.storage = storage
        self.aanvragen = aanvragen if aanvragen else self.__read_from_storage()
        self.__sort_aanvragen() 
    def __read_from_storage(self):
        logInfo('Start reading aanvragen from database')
        result = self.storage.read_aanvragen()
        logInfo('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        self.aanvragen.sort(key=lambda a:a.timestamp, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)

