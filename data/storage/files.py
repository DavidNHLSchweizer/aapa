from __future__ import annotations
from enum import Enum, auto
from data.storage.mappers import ColumnMapper, FilenameColumnMapper, TableMapper, TimeColumnMapper
from data.storage.storage_const import DBtype
from data.aapa_database import FilesTableDefinition
from data.classes.files import File, Files
from data.storage.storage_base import StorageBase, StorageException
from data.table_registry import register_table
from database.database import Database
from database.dbConst import EMPTY_ID
from general.log import log_debug, log_exception
from general.timeutil import TSC


class FileSync:
    class Strategy(Enum):
        IGNORE  = auto()
        DELETE  = auto()
        CREATE  = auto()
        UPDATE  = auto()
        REPLACE = auto()      
    def __init__(self, files: FilesStorage):
        self.files = files
    def __check_known_file(self, file: File)->bool:
        if (stored_file := self.files.find_name(filename=file.filename)):
            if stored_file.aanvraag_id != EMPTY_ID and stored_file.aanvraag_id != file.aanvraag_id:
                log_exception(f'file {stored_file.filename} bestaat al voor aanvraag {stored_file.aanvraag_id}', StorageException)
            elif stored_file.filetype not in {File.Type.UNKNOWN, File.Type.INVALID_PDF}:  
                return False 
            return True
        return False
    def get_strategy(self, old_files: Files, new_files: Files)->dict[File.Type]:
        result = {ft: FileSync.Strategy.IGNORE for ft in File.Type}
        old_filetypes = {ft for ft in old_files.get_filetypes()} 
        log_debug(f'old_filetypes: {old_filetypes}' )
        new_filetypes = {ft for ft in new_files.get_filetypes()} 
        log_debug(f'new_filetypes: {new_filetypes}' )
        for file in new_files.files:
            if self.__check_known_file(file):
                new_filetypes.remove(file.filetype) # don't reprocess
                result[file.filetype] = FileSync.Strategy.REPLACE
        for ft in old_filetypes.difference(new_filetypes):
            result[ft] = FileSync.Strategy.DELETE
        for ft in new_filetypes.difference(old_filetypes):
            result[ft] = FileSync.Strategy.CREATE
            new_filetypes.remove(ft)
        for ft in new_filetypes: 
            if old_files.get_file(ft) != new_files.get_file(ft):
                result[ft] = FileSync.Strategy.UPDATE
        summary_str = "\n".join([f'{ft}: {str(result[ft])}' for ft in File.Type if result[ft]!=FileSync.Strategy.IGNORE])
        log_debug(f'Strategy: {summary_str}')
        return result
    
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
                assert stored.aanvraag_id == EMPTY_ID
                result = FileStorageRecord.Status.STORED_INVALID
            elif stored.digest != self.digest:
                assert stored.aanvraag_id != EMPTY_ID
                result = FileStorageRecord.Status.MODIFIED
            else:
                assert stored.aanvraag_id != EMPTY_ID
                result = FileStorageRecord.Status.STORED
        return result
    def __analyse_stored_digest(self, stored: File)->FileStorageRecord.Status:
        if stored is None:
            result = FileStorageRecord.Status.UNKNOWN
        else:
            self.stored = stored
            if stored.filetype == File.Type.INVALID_PDF:
                assert stored.aanvraag_id == EMPTY_ID
                result = FileStorageRecord.Status.STORED_INVALID_COPY
            else:
                assert stored.aanvraag_id != EMPTY_ID      
                result = FileStorageRecord.Status.DUPLICATE
        return result
    def analyse(self, storage: FilesStorage)->FileStorageRecord:
        self.status = self.__analyse_stored_name(storage.find_filename(self.filename))
        if self.status == FileStorageRecord.Status.UNKNOWN:
            self.status = self.__analyse_stored_digest(storage.find_digest(self.digest))
        return self

class FileTypeColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->File.Type:
        return File.Type(db_value)

class FilesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'filename': return FilenameColumnMapper(column_name)
            case 'timestamp': return TimeColumnMapper(column_name) 
            case 'filetype': return FileTypeColumnMapper(column_name)
            case _: return super()._init_column_mapper(column_name, database)

class FilesStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, File, autoID=True)
        self.sync_strategy = FileSync(self)
    def find_all_for_filetype(self, filetypes: File.Type | set[File.Type], aanvraag_id:int = None)->Files:
        log_debug(f'find_all_for_filetype {filetypes} {aanvraag_id}')
        # if isinstance(filetypes, set):
        #     place_holders = f' in ({",".join("?"*len(filetypes))})' 
        #     params = [ft for ft in filetypes]
        # else:
        #     place_holders = '=?'
        #     params = [filetypes]
        # if aanvraag_id:
        #     place_holders += ' and aanvraag_id=?'
        #     params.append(aanvraag_id)        
        result = Files(aanvraag_id)
        for row in self.query_builder.find_id_from_values(attributes=['aanvraag_id','filetype'], values=[aanvraag_id, filetypes]):
        # for row in self.database._execute_sql_command(f'select id from {self.table_name} where filetype' + place_holders, params, True):
            result.set_file(self.read(row['id'])) #check hier, komen de ids wel mee?
        return result
    def get_storage_record(self, filename: str)->FileStorageRecord:
        return FileStorageRecord(filename).analyse(self)
    def find_digest(self, digest: str)->File:
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
                            filetype=filetype, aanvraag_id=EMPTY_ID)
            self.create(new_file)
            result = new_file
        return result
    
register_table(class_type=File, table=FilesTableDefinition(), mapper_type=FilesTableMapper, autoID=True)