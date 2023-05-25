import datetime
from data.classes import AanvraagInfo, FileInfo, FileType
from data.storage import AAPStorage
from general.log import logInfo

class AanvraagProcessor:
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        self.storage = storage
        self.aanvragen = aanvragen if aanvragen else self.__read_from_storage()
        self.__sort_aanvragen() 
        self.known_files = self.__init_known_files(self.aanvragen)
        for fileinfo in storage.file_info.find_all_for_filetype(FileType.INVALID_PDF):
            self.known_files[fileinfo.filename] = fileinfo
    def known_file_info(self, filename: str)->FileInfo:
        if fileinfo := self.known_files.get(str(filename), None):
            return fileinfo
        else:
            return None
    def __init_known_files(self, aanvragen: list[AanvraagInfo]):
        result = {}
        for aanvraag in aanvragen:
            for ft in FileType:
                if ft != FileType.UNKNOWN and (fn := aanvraag.files.get_filename(ft)):                    
                    result[str(fn)] = aanvraag.files.get_info(ft)
        return result        
    def __read_from_storage(self):
        logInfo('Start reading aanvragen from database')
        result = self.storage.aanvragen.read_all()
        logInfo('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        def comparekey(a: AanvraagInfo):
            if isinstance(a.timestamp, datetime.datetime):
                return a.timestamp
            else:
                return datetime.datetime.now()
        # self.aanvragen.sort(key=lambda a:a.timestamp, reverse=True)
        self.aanvragen.sort(key=comparekey, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)

