from data.aanvraag_info import AanvraagInfo, FileInfo, FileType
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
        self.known_files = self.__init_known_files(self.aanvragen)
        for fileinfo in storage.find_invalid_fileinfos(FileType.INVALID_PDF):
            self.known_files[fileinfo.filename] = fileinfo
    def known_file_info(self, filename: str)->FileInfo:
        # print(f'testing: {filename}') 
        # for fn,fi in self.known_files.items():
        #     print(f'{fn} ({fi.filename})')
        if fileinfo := self.known_files.get(str(filename), None):
            # print(f'found: {fileinfo}')
            return fileinfo
        else:
            # print('not found')
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

