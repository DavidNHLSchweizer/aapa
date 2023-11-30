from __future__ import annotations
from enum import Enum, auto
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper, TableMapper, TimeColumnMapper
from data.aapa_database import FilesTableDefinition
from data.classes.files import File
from data.storage.extended_crud import ExtendedCRUD
from data.storage.CRUDs import register_crud
from database.database import Database
from database.dbConst import EMPTY_ID
from general.log import log_debug
from general.timeutil import TSC

class FileStorageRecord:
    class Status(Enum):
        UNKNOWN             = auto()
        STORED              = auto()
        STORED_INVALID      = auto()
        STORED_INVALID_COPY = auto()
        DUPLICATE           = auto()
        MODIFIED            = auto()
    def __init__(self, filename: str):
        self.filename = filename
        self.digest = File.get_digest(filename)
        self.stored = None
        self.status = FileStorageRecord.Status.UNKNOWN
    def __analyse_stored_name(self, stored: File)->FileStorageRecord.Status:
        if stored is None:
            result = FileStorageRecord.Status.UNKNOWN
        else:
            self.stored = stored
            if stored.filetype == File.Type.INVALID_PDF:
                result = FileStorageRecord.Status.STORED_INVALID
            elif stored.digest != self.digest:
                result = FileStorageRecord.Status.MODIFIED
            else:
                result = FileStorageRecord.Status.STORED
        return result
    def __analyse_stored_digest(self, stored: list[File])->FileStorageRecord.Status:
        if stored is None:
            result = FileStorageRecord.Status.UNKNOWN
        else:
            for stored_file in stored:
                if stored_file.filetype == File.Type.INVALID_PDF:
                    result = FileStorageRecord.Status.STORED_INVALID_COPY
                    self.stored = stored_file
                else:
                    result = FileStorageRecord.Status.DUPLICATE
                    self.stored = stored_file
        return result
    def analyse(self, storage: FilesStorage)->FileStorageRecord:
        self.status = self.__analyse_stored_name(storage.find_filename(self.filename))
        if self.status == FileStorageRecord.Status.UNKNOWN:
            self.status = self.__analyse_stored_digest(storage.find_digest(self.digest))
        return self

class FilesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'filename': return FilenameColumnMapper(column_name)
            case 'timestamp': return TimeColumnMapper(column_name) 
            case 'filetype': return ColumnMapper(column_name=column_name, db_to_obj=File.Type)
            case _: return super()._init_column_mapper(column_name, database)

class FilesStorage(ExtendedCRUD):
    def find_all_for_filetype(self, filetypes: File.Type | set[File.Type])->list[File]:
        log_debug(f'find_all_for_filetype {filetypes}')
        result = []
        for id in self.query_builder.find_id_from_values(attributes=['filetype'], values=[filetypes]):
            result.append(self.read(id)) #check hier, komen de ids wel mee?
        return result
    def get_storage_record(self, filename: str)->FileStorageRecord:
        return FileStorageRecord(filename).analyse(self)
    def find_digest(self, digest: str)->list[File]:

        return self.find_value('digest', digest)
    def find_filename(self, filename: str)->File:
        return self.find_value('filename', filename)
    def store_invalid(self, filename: str, filetype = File.Type.INVALID_PDF)->File:
        log_debug('store_invalid')
        if (stored:=self.find_filename(filename)):
            stored.filetype = filetype
            stored.aanvraag_id=EMPTY_ID
            self.update(stored)
            result = stored
        else:
            new_file = File(filename, timestamp=TSC.AUTOTIMESTAMP, digest=File.AUTODIGEST, 
                            filetype=filetype)
            self.create(new_file)
            result = new_file
        return result
    def is_known_invalid(self, filename: str)->bool:
        if (stored:=self.find_filename(filename)):
            return File.Type.is_invalid(stored.filetype)
        else:
            return False     

register_crud(class_type=File, 
                table=FilesTableDefinition(), 
                mapper_type=FilesTableMapper,
                crud=FilesStorage)
                