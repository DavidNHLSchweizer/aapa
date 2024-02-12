from __future__ import annotations
from ast import Tuple
from enum import Enum, auto
from data.classes.files import File
from storage.general.CRUDs import CRUD, CRUDQueries
from storage.general.storage_const import StorageException
from general.log import log_debug

class FileStorageAnalyzer:
    class Status(Enum):
        UNKNOWN             = auto()
        STORED              = auto()
        STORED_INVALID      = auto()
        STORED_INVALID_COPY = auto()
        DUPLICATE           = auto()
        MODIFIED            = auto()
    def __init__(self, queries: FilesQueries):
        self.queries = queries
    def __analyze_stored_name(self, filename: str)->Tuple[Status,File]:
        result_status = FileStorageAnalyzer.Status.UNKNOWN
        result_file:File = None
        if (stored := self.queries.find_values('filename', filename)):
            if len(stored) > 1:
                raise StorageException(f'Duplicate file {filename} in storage.')
            result_file: File = stored[0]
            if result_file.filetype == File.Type.INVALID_PDF:
                result_status = FileStorageAnalyzer.Status.STORED_INVALID
            elif result_file.digest != File.get_digest(filename):
                result_status = FileStorageAnalyzer.Status.MODIFIED
            else:
                result_status = FileStorageAnalyzer.Status.STORED
        return result_status,result_file
    def __analyze_stored_digest(self, filename)->Tuple[Status,File]:
        result_status = FileStorageAnalyzer.Status.UNKNOWN
        result_file   = None
        if stored := self.queries.find_values('digest', File.get_digest(filename)):
            #note: there might be more than one, which is not necessarily an error!
            # files could be copied, e.g. the Aanvraag source file is copied to the FORMS directory
            for stored_file in stored:
                if stored_file.filetype == File.Type.INVALID_PDF:
                    result_status = FileStorageAnalyzer.Status.STORED_INVALID_COPY
                    result_file = stored_file
                else:
                    result_status = FileStorageAnalyzer.Status.DUPLICATE
                    result_file = stored_file
        return result_status,result_file
    def analyze(self, filename)->Tuple[Status,File]:        
        status,stored = self.__analyze_stored_name(filename)
        if status == FileStorageAnalyzer.Status.UNKNOWN:
            status,stored = self.__analyze_stored_digest(filename)
        log_debug(f'ANALYZE result: {status} {stored}')
        return (status,stored)

class FilesQueries(CRUDQueries):
    def __init__(self, crud: CRUD):
        super().__init__(crud)
        self.known_files:list[File] = None 
    def analyze(self, filename: str)->Tuple[FileStorageAnalyzer.Status,File]:
        return FileStorageAnalyzer(self).analyze(str(filename))
    def is_known_file(self, filename: str)->bool:
        return self.find_ids_where(where_attributes=['filename', 'filetype'], where_values=[filename,File.Type.valid_file_types()]) != []
    # def is_known_file(self, filename: str)->bool: 
    #     if not self.known_files:
    #         self.known_files:list[File] = self.find_values(attributes='filetype', 
    #                                 values=File.Type.valid_file_types(), read_many=True)
    #     return filename in {file.filename for file in self.known_files} or \
    #         self.find_values('files', attributes=['filename', 'filetype'], 
    #                                  values=[str(filename), File.Type.invalid_file_types()], read_many=True) != []
