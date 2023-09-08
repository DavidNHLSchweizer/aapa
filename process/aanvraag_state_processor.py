
from abc import ABC, abstractmethod
import datetime
from data.classes import AanvraagInfo, FileInfo, FileType
from data.storage import AAPStorage
from general.log import log_info
from general.preview import Preview


class NewAanvraagProcessor(ABC):
    @abstractmethod
    def process(self, aanvraag: AanvraagInfo, preview = False, **kwargs)->bool:
        return False
    def must_process(self, aanvraag: AanvraagInfo, **kwargs)->bool:
        return True

class NewAanvragenProcessor:
    def __init__(self, processors: NewAanvraagProcessor|list[NewAanvraagProcessor], storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        self._processors:list[NewAanvraagProcessor] = []
        if isinstance(processors, list):
            for processor in processors: self._processors.append(processor)
        else:
            self._processors.append(processors)
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
        log_info('Start reading aanvragen from database')
        result = self.storage.aanvragen.read_all()
        log_info('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        def comparekey(a: AanvraagInfo):
            if isinstance(a.timestamp, datetime.datetime):
                return a.timestamp
            else:
                return datetime.datetime.now()
        self.aanvragen.sort(key=comparekey, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)
    def process(self, preview=False, filter_func = None, **kwargs)->int:
        n_processed = 0
        with Preview(preview):
            for aanvraag in self.filtered_aanvragen(filter_func):
                aanvraag_processed = True
                for processor in self._processors:
                    if processor.must_process(aanvraag, preview) and not processor.process(aanvraag, preview, **kwargs):                        
                        aanvraag_processed = False
                        break
                    self.storage.aanvragen.update(aanvraag)
                    self.storage.commit()
                if aanvraag_processed:
                    n_processed += 1
        return n_processed

