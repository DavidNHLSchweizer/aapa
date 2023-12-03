from __future__ import annotations
from enum import Enum, auto
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper, TableMapper, TimeColumnMapper
from data.aapa_database import FilesTableDefinition
from data.classes.files import File
from data.storage.CRUDs import CRUDQueries, register_crud
from data.storage.general.storage_const import StorageException
from database.database import Database
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
    def __analyse_stored_name(self, stored: list[File])->FileStorageRecord.Status:
        if stored is []:
            result = FileStorageRecord.Status.UNKNOWN
        else:
            assert len(stored) == 1
            self.stored = stored[0]
            if self.stored.filetype == File.Type.INVALID_PDF:
                result = FileStorageRecord.Status.STORED_INVALID
            elif self.stored.digest != self.digest:
                result = FileStorageRecord.Status.MODIFIED
            else:
                result = FileStorageRecord.Status.STORED
        return result
    def __analyse_stored_digest(self, stored: list[File])->FileStorageRecord.Status:
        if stored is []:
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
    def analyse(self, filenames:list[str], digests:list[str])->FileStorageRecord:
        self.status = self.__analyse_stored_name(filenames)
        if self.status == FileStorageRecord.Status.UNKNOWN:
            self.status = self.__analyse_stored_digest(digests)
        return self

class FilesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'filename': return FilenameColumnMapper(column_name)
            case 'timestamp': return TimeColumnMapper(column_name) 
            case 'filetype': return ColumnMapper(column_name=column_name, db_to_obj=File.Type)
            case _: return super()._init_column_mapper(column_name, database)

class FilesCRUDhelper(CRUDQueries):pass

register_crud(class_type=File, 
                table=FilesTableDefinition(), 
                mapper_type=FilesTableMapper,
                queries_type=FilesCRUDhelper
                )
                