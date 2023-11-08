from __future__ import annotations
from enum import Enum, auto
from typing import Iterable, Type
from data.AAPdatabase import  create_root
from data.classes.aanvragen import Aanvraag
from data.classes.base_dirs import BaseDir
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.milestones import StudentMilestone
from data.classes.studenten import Student
from data.classes.action_log import ActionLog
from data.classes.verslagen import Verslag
from data.crud.aanvragen import CRUD_aanvragen
from data.crud.base_dirs import CRUD_basedirs
from data.crud.bedrijven import  CRUD_bedrijven
from data.crud.files import CRUD_files
from data.crud.action_log import CRUD_action_log, CRUD_action_log_aanvragen, CRUD_action_log_invalid_files, CRUD_action_log_relations
from data.crud.studenten import CRUD_studenten
from data.crud.crud_base import AAPAClass, CRUDbase, KeyClass
from data.crud.verslagen import CRUD_verslagen
from database.database import Database
from database.dbConst import EMPTY_ID
from data.roots import add_root, encode_path
from general.log import log_debug, log_error, log_exception, log_warning
from general.timeutil import TSC

class StorageException(Exception): pass

class ObjectStorage:
    def __init__(self, database: Database, crud: CRUDbase):
        self.database = database
        self.crud  = crud
    def create(self, object: AAPAClass):
        self.crud.create(object)
    def read(self, key)->AAPAClass:
        return self.crud.read(key)
    def update(self, object: AAPAClass):
        self.crud.update(object)
    def delete(self, key: KeyClass):
        self.crud.delete(key)
    @property
    def table_name(self)->str:
        return self.crud.table.name
    def max_id(self):
        if (row := self.database._execute_sql_command(f'select max(id) from {self.table_name}', [], True)) and row[0][0]:
            return row[0][0]           
        else:
            return 0                    
        
class BedrijvenStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_bedrijven(database))
    def create(self, bedrijf: Bedrijf):
        if row:= self.database._execute_sql_command(f'select * from {self.table_name} where (name=?)', [bedrijf.name], True):
            bedrijf.id = row[0]['id']
        else:
            super().create(bedrijf)

class StudentenStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_studenten(database))
    def create(self, student: Student):
        if row:= self.database._execute_sql_command(f'select * from {self.table_name} where (stud_nr=? or full_name=? or email=?)', 
                                                    [student.stud_nr, student.full_name, student.email], True):
            student.id = row[0]['id']
        else:
            super().create(student)
    def find_by_column_value(self, column_name: str, value: str)->Student:
        if row:=self.database._execute_sql_command(f'select id from {self.table_name} where ({column_name}=?)', [value], True):
            return self.read(row[0][0])
        return None
    def find_student_by_name_or_email(self, student: Student)->Student:
        for column_name in ['full_name', 'email']:
            if result:=self.find_by_column_value(column_name, getattr(student, column_name)):
                return result
        return None        
    def create_unique_student_nr(self, student: Student)->str:
        n = 1
        if not (result := student.stud_nr):
            result = f'{student.initials()}{n}'
        while self.find_by_column_value('stud_nr', result) is not None:
            n+=1
        return result

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
        for file in new_files.get_files():
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
        self.status = self.__analyse_stored_name(storage.find_name(self.filename))
        if self.status == FileStorageRecord.Status.UNKNOWN:
            self.status = self.__analyse_stored_digest(storage.find_digest(self.digest))
        return self
    
class FilesStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_files(database))
        self.sync_strategy = FileSync(self)
    @property
    def crud_files(self)->CRUD_files:
        return self.crud
    def create(self, file: File):
        if (ids := self._find_name_id(file.filename)):            
            stored_file = self.read(ids[0])
            if stored_file.aanvraag_id == file.aanvraag_id:
                log_debug(f'file already there, doing nothing {stored_file}')
                #this is probably an error!
            else:
                log_debug(f'already file in create: [{ids}]')
                # self.duplicate_warning(file, stored_file)                
        else:
            log_debug(f'creating new file [{file}]')
            super().create(file)
    def _find_name_id(self, filename: str)->Iterable[int]:
        if rows := self.database._execute_sql_command(f'select id from {self.table_name} where filename=? order by id desc', [self.crud_files.map_object_to_db('filename', filename)], True):
            result = []
            for row in rows:
                result.append(row['id'])
            return result
        return None                                    
    def find_name(self, filename: str)->File:
        if ids := self._find_name_id(filename):
            return self.read(ids[0])
        return None                                                     
    def __load(self, aanvraag_id: int, filetypes: set[File.Type])->Iterable[File]:
        log_debug('__load')
        params = [aanvraag_id]
        params.extend([ft for ft in filetypes])
        if rows:= self.database._execute_sql_command(f'select id from {self.table_name} where aanvraag_id=? and filetype in (' + ','.join('?'*len(filetypes))+')', params, True):
            file_IDs=[row["id"] for row in rows]
            log_debug(f'found: {file_IDs}')
            result = [self.crud_files.read(id) for id in file_IDs]
            return result
        return []
    def find_all(self, aanvraag_id: int)->Files:
        log_debug('find_all')
        result = Files(aanvraag_id)
        filetypes = {ft for ft in File.Type if ft != File.Type.UNKNOWN}
        result.reset_file(filetypes)
        if files := self.__load(aanvraag_id, filetypes):
            for file in files:
                result.set_file(file)
        return result        
    def find_all_for_filetype(self, filetypes: File.Type | set[File.Type], aanvraag_id:int = None)->Files:
        log_debug(f'find_all_for_filetype {filetypes} {aanvraag_id}')
        if isinstance(filetypes, set):
            place_holders = f' in ({",".join("?"*len(filetypes))})' 
            params = [ft for ft in filetypes]
        else:
            place_holders = '=?'
            params = [filetypes]
        if aanvraag_id:
            place_holders += ' and aanvraag_id=?'
            params.append(aanvraag_id)
        result = Files(aanvraag_id)
        for row in self.database._execute_sql_command(f'select id from {self.table_name} where filetype' + place_holders, params, True):
            result.set_file(self.read(row['id'])) #check hier, komen de ids wel mee?
        return result
    def find_digest(self, digest)->File:
        log_debug('find_digest')
        if row:= self.database._execute_sql_command(f'select id from {self.table_name} where digest=?', [digest], True):
            file = self.read(row[0]["id"])
            log_debug(f'success: {file}')
            return file
    def sync_storage_files(self, aanvraag_id, new_files: Files, filetypes: set[File.Type]=None):
        log_debug('sync_storage_files')
        for file in new_files.get_files():
            file.aanvraag_id = aanvraag_id
        old_files = self.find_all_for_filetype(filetypes, aanvraag_id=aanvraag_id)
        for file in old_files.get_files():
            log_debug(f'F: {file} {file.id}')
        strategy = self.sync_strategy.get_strategy(old_files, new_files)
        for filetype in strategy.keys():
            match strategy[filetype]:
                case FileSync.Strategy.IGNORE: pass
                case FileSync.Strategy.DELETE:
                    self.delete(old_files.get_id(filetype))
                case FileSync.Strategy.CREATE:
                    self.create(new_files.get_file(filetype))
                case FileSync.Strategy.UPDATE:
                    self.update(new_files.get_file(filetype))
                case FileSync.Strategy.REPLACE:
                    old_id = self._find_name_id(new_files.get_filename(filetype))[0]
                    self.delete(old_id)
                    self.create(new_files.get_file(filetype))
        log_debug('END sync')
    def delete_all(self, aanvraag_id):
        if (all_files := self.__load(aanvraag_id, {ft for ft in File.Type if ft != File.Type.UNKNOWN})) is not None:
            for file in all_files:
                self.delete(file.id)
    def is_duplicate(self, filename: str, digest: str):
        return (stored:=self.find_digest(digest)) is not None and filename != stored.filename
    def known_file(self, filename: str)->File:
        return self.find_digest(File.get_digest(filename))
    def read_filename(self, filename: str)->File:
        files = self.crud_files
        if (rows:=self.database._execute_sql_command(f'select id from {files.table.name} where filename=?', [files.map_object_to_db('filename', filename)],True)):
            result =  files.read(rows[0][0])
            return result
        return None
    def store_invalid(self, filename: str, filetype = File.Type.INVALID_PDF)->File:
        log_debug('store_invalid')
        if (stored:=self.read_filename(filename)):
            stored.filetype = filetype
            stored.aanvraag_id=EMPTY_ID
            self.update(stored)
            result = stored
        else:
            new_file = File(filename, timestamp=TSC.AUTOTIMESTAMP, digest=File.AUTODIGEST, filetype=filetype, aanvraag_id=EMPTY_ID)
            self.create(new_file)
            result = new_file
        self.database.commit()
        return result
    def is_known_invalid(self, filename, filetype = File.Type.INVALID_PDF):
        if (stored:=self.read_filename(filename)):
            return stored.filetype == filetype
        else:
            return False     
    def get_storage_record(self, filename: str)->FileStorageRecord:
        return FileStorageRecord(filename).analyse(self)

class AanvraagStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_aanvragen(database))
        self.files = FilesStorage(database)
        self.bedrijven = BedrijvenStorage(database)
        self.studenten = StudentenStorage(database)
    def create(self, aanvraag: Aanvraag):
        self.__create_table_references(aanvraag)
        # aanvraag.files.set_info(source_file)
        aanvraag.aanvraag_nr = self.__count_student_aanvragen(aanvraag) + 1
        super().create(aanvraag)
        log_debug('sync_files (CREATE)')
        self.sync_files(aanvraag, {File.Type.AANVRAAG_PDF})
        log_debug('ready create')
    def sync_files(self, aanvraag: Aanvraag, filetypes: set[File.Type]=None):
        self.files.sync_storage_files(aanvraag_id=aanvraag.id, new_files=aanvraag.files, 
                        filetypes=filetypes if filetypes else ({filetype for filetype in File.Type} - {File.Type.UNKNOWN, File.Type.INVALID_PDF}))
    def read(self, id: int)->Aanvraag:
        aanvraag = super().read(id)
        aanvraag.files = self.files.find_all(aanvraag.id)
        return aanvraag
    def update(self, aanvraag: Aanvraag):
        self.__create_table_references(aanvraag)        
        super().update(aanvraag)
        log_debug('sync_files (UPDATE)')
        self.sync_files(aanvraag)
    def delete(self, id: int):
        self.files.delete_all(id)
        super().delete(id)
    def __read_all_filtered(self, aanvragen: Iterable[Aanvraag], filter_func = None)->Iterable[Aanvraag]:
        if not filter_func:
            return aanvragen
        else:
            return list(filter(filter_func, aanvragen))
    def __read_all_all(self, filter_func = None)->Iterable[Aanvraag]:
        if row:= self.database._execute_sql_command(f'select id from {self.table_name} where status != ?', [Aanvraag.Status.DELETED], True):            
            return self.__read_all_filtered([self.read(r['id']) for r in row], filter_func=filter_func)
        else:
            return None
    def __read_all_states(self, states:set[Aanvraag.Status]=None, filter_func = None)->Iterable[Aanvraag]:
        params = [state.value for state in states]
        if row:= self.database._execute_sql_command(f'select id from {self.table_name} where status in ({",".join(["?"]*len(params))})', params, True):
            return self.__read_all_filtered([self.read(r['id']) for r in row], filter_func=filter_func)
    def read_all(self, filter_func = None, states:set[Aanvraag.Status]=None)->Iterable[Aanvraag]:
        if not states:
            return self.__read_all_all(filter_func=filter_func)        
        else: 
            return self.__read_all_states(filter_func=filter_func, states=states)
    def find_student_bedrijf(self, student: Student, bedrijf: Bedrijf, filter_func=None)->Iterable[Aanvraag]:
        return self.read_all(filter_func=lambda a: filter_func(a) and a.student.id == student.id and a.bedrijf.id == bedrijf.id)
    def find_student(self, student: Student)->Iterable[Aanvraag]:
        return self.read_all(filter_func = lambda a: a.student.id == student.id)
    def __count_student_aanvragen(self, aanvraag: Aanvraag):
        if (row := self.database._execute_sql_command(f'select count(id) from {self.table_name} where stud_id=? and status!=?', [aanvraag.student.id,Aanvraag.Status.DELETED], True)):
            return row[0][0]
        else:
            return 0    
    def __create_table_references(self, aanvraag: Aanvraag):
        if (not self.bedrijven.read(aanvraag.bedrijf.id)) and \
            (row:= self.database._execute_sql_command(f'select * from {self.bedrijven.table_name} where (name=?)', [aanvraag.bedrijf.name], True)):
            aanvraag.bedrijf.id = row[0]['id']
        else:
            self.bedrijven.create(aanvraag.bedrijf)
        if not (self.studenten.read(aanvraag.student.id)):
            self.studenten.create(aanvraag.student)

class ActionLogRelationStorage:
    def __init__(self, crud: CRUD_action_log_relations, rel_storage: ObjectStorage, add_method: str):
        self.crud = crud
        self.rel_storage = rel_storage
        self.add_method = add_method
    def create(self, action_log: ActionLog):
        self.crud.create(action_log)
    def add_object(self, action_log: ActionLog, object: AAPAClass):
        if method := getattr(action_log, self.add_method, None):
            method(object)
    def read(self, action_log: ActionLog):
        for record in self.crud.read(action_log.id):
            self.add_object(action_log, self.rel_storage.read(record.rel_id))
    def update(self, action_log: ActionLog):
        self.crud.update(action_log)
    def delete(self, id: int):
        self.crud.delete(id)

class ActionLogAanvragenStorage(ActionLogRelationStorage):
    def __init__(self, database: Database):
        super().__init__(CRUD_action_log_aanvragen(database), AanvraagStorage(database), 'add_aanvraag')

class ActionLogInvalidFilesStorage(ActionLogRelationStorage):
    def __init__(self, database: Database):
        super().__init__(CRUD_action_log_invalid_files(database), FilesStorage(database), 'add_invalid_file')

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'
class ActionLogStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_action_log(database))
        self.relations: list[ActionLogRelationStorage] = [ActionLogAanvragenStorage(database), ActionLogInvalidFilesStorage(database)]
    def create(self, action_log: ActionLog):
        super().create(action_log)
        for relation in self.relations:
            relation.create(action_log)
    def read(self, id: int)->ActionLog:
        result: ActionLog = super().read(id)
        for relation in self.relations:
            relation.read(result)
        return result
    def update(self, action_log: ActionLog):
        super().update(action_log)
        for relation in self.relations:
            relation.update(action_log)
    def delete(self, id: int):
        for relation in self.relations:
            relation.delete(id)
        super().delete(id)
    def _find_action_log(self, id: int = EMPTY_ID)->ActionLog:
        if id == EMPTY_ID:
            if (row := self.database._execute_sql_command(f'select id from {self.table_name} where can_undo = ? group by can_undo having max(id)', [1], True)):
                id = row[0][0]
            if id is None or id == EMPTY_ID:
                log_warning(NoUNDOwarning)
                return None
        return self.read(id)
    def last_action(self)->ActionLog:
        return self._find_action_log()

class VerslagStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_verslagen(database))
        self.files = FilesStorage(database)
        self.studenten = StudentenStorage(database)
    def create(self, verslag: Verslag):
        self.__create_table_references(verslag)
        super().create(verslag)
        log_debug('sync_files (CREATE)')
        self.sync_files(verslag, {File.Type.AANVRAAG_PDF})
        log_debug('ready create')
    def sync_files(self, verslag: Verslag, filetypes: set[File.Type]=None):
        pass # to be determined
        # self.files.sync_storage_files(aanvraag_id=aanvraag.id, new_files=aanvraag.files, 
        #                 filetypes=filetypes if filetypes else ({filetype for filetype in File.Type} - {File.Type.UNKNOWN, File.Type.INVALID_PDF}))
    def read(self, id: int)->Verslag:
        verslag = super().read(id)
        verslag.files = self.files.find_all(verslag.id)
        return verslag
    def update(self, verslag: Verslag):
        self.__create_table_references(verslag)        
        super().update(verslag)
        log_debug('sync_files (UPDATE)')
        self.sync_files(verslag)
    def delete(self, id: int):
        self.files.delete_all(id)
        super().delete(id)  
    def __create_table_references(self, verslag: Verslag):
        if not self.studenten.read(verslag.student.id):
            self.studenten.create(verslag.student)

class BaseDirStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_basedirs(database))
    def read_all(self)->Iterable[BaseDir]:
        if (rows := self.database._execute_sql_command('select id from BASEDIRS', [],True)):
            return [self.crud.read(row['id']) for row in rows] 
        return None

class AAPAStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self.aanvragen = AanvraagStorage(database)
        self.action_logs = ActionLogStorage(database)
        self.verslagen = VerslagStorage(database)
        self.basedirs = BaseDirStorage(database)
    @property
    def files(self)->FilesStorage:
        return self.aanvragen.files
    @property
    def studenten(self)->StudentenStorage:
        return self.aanvragen.studenten
    def add_file_root(self, root: str, code = None)->str:
        encoded_root = encode_path(root)
        code = add_root(encoded_root, code)
        if encoded_root != code: 
        #this means the root is already registered, re-encoding causes it to reduce to just the code
            create_root(self.database, code, encoded_root)
            self.commit()
    def commit(self):
        self.database.commit()