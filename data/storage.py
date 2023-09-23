from data.AAPdatabase import  create_root
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from data.classes.process_log import ProcessLog
from data.crud.aanvragen import CRUD_aanvragen
from data.crud.bedrijven import  CRUD_bedrijven
from data.crud.files import CRUD_files
from data.crud.process_log import CRUD_process_log, CRUD_process_log_aanvragen
from data.crud.studenten import CRUD_studenten
from data.crud.crud_base import AAPAClass, CRUDbase, KeyClass
from database.database import Database
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
from data.roots import add_root, encode_path
from general.log import log_info, log_warning
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
    def max_id(self):
        if (row := self.database._execute_sql_command(f'select max(id) from {self.crud.table.table_name}', [], True)) and row[0][0]:
            return row[0][0]           
        else:
            return 0                    
        
class BedrijvenStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_bedrijven(database))
    def create(self, bedrijf: Bedrijf):
        if row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [bedrijf.name], True):
            bedrijf.id = row[0]['id']
        else:
            super().create(bedrijf)

class StudentenStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_studenten(database))

class FilesStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_files(database))
    def find(self, aanvraag_id: int, filetype: File.Type)->File:
        if row:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype=?', 
                [aanvraag_id, filetype], True):
            file = self.read(row[0]["filename"])
            log_info(f'success: {file}')
            return file
        return None
    @property
    def crud_files(self)->CRUD_files:
        return self.crud
    def __load(self, aanvraag_id: int, filetypes: set[File.Type])->list[File]:
        params = [aanvraag_id]
        params.extend([ft for ft in filetypes])
        if rows:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype in (' + ','.join('?'*len(filetypes))+')', params, True):
            filenames=[row["filename"] for row in rows]
            result = self.crud_files.read_all(filenames)
            return result
        return None
    def find_all(self, aanvraag_id: int)->Files:
        result = Files(aanvraag_id)
        filetypes = {ft for ft in File.Type if ft != File.Type.UNKNOWN}
        result.reset_file(filetypes)
        for file in self.__load(aanvraag_id, filetypes):
            if file:
                result.set_file(file)
        return result        
    def find_all_for_filetype(self, filetypes: File.Type | set[File.Type])->list[File]:
        if isinstance(filetypes, set):
            place_holders = f' in ({",".join("?"*len(filetypes))})' 
            params = [ft for ft in filetypes]
        else:
            place_holders = '=?'
            params = [filetypes]
        result = []
        for row in self.database._execute_sql_command('select filename from FILES where filetype' + place_holders, params, True):
            result.append(self.read(row['filename']))
        return result
    def find_digest(self, digest)->File:
        if row:= self.database._execute_sql_command('select filename from FILES where digest=?', [digest], True):
            file = self.read(row[0]["filename"])
            log_info(f'success: {file}')
            return file
    def sync(self, aanvraag_id, file: File):
        file.aanvraag_id = aanvraag_id
        if (cur_file:=self.find(aanvraag_id, file.filetype)) is not None:
            #file currently exists in database
            if file.filename:
                self.update(file)
            else:
                self.delete(cur_file.filename)
        elif file.filename:            
            if (cur_file := self.read(file.filename)):
                #file is known in database, PROBABLY (!?) not linked to aanvraag 
                log_warning(f'bestand {summary_string(file.filename, maxlen=80)} is bekend in database:\n\t{cur_file.summary()}.\nWordt vervangen door\n\t{file.summary()}')
                self.update(file)
            else:
                #new file
                self.create(file)
    def delete_all(self, aanvraag_id):
        if (all_files := self.__load(aanvraag_id, {ft for ft in File.Type if ft != File.Type.UNKNOWN})) is not None:
            for file in all_files:
                self.delete(file.filename)
    def is_duplicate(self, file: File):
        return (stored:=self.read(file.filename)) is not None and stored.digest == file.digest
    def known_file(self, filename: str)->File:
        return self.find_digest(File.get_digest(filename))
    def store_invalid(self, filename):
        if (stored:=self.read(filename)):
            stored.filetype = File.Type.INVALID_PDF
            stored.aanvraag_id=EMPTY_ID
            self.update(stored)
        else:
            self.create(File(filename, timestamp=TSC.AUTOTIMESTAMP, digest=File.AUTODIGEST, filetype=File.Type.INVALID_PDF, aanvraag_id=EMPTY_ID))
        self.database.commit()
    def is_known_invalid(self, filename):
        if (stored:=self.read(filename)):
            return stored.filetype == File.Type.INVALID_PDF
        else:
            return False     

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
        self.sync_files(aanvraag, {File.Type.AANVRAAG_PDF})
    def sync_files(self, aanvraag: Aanvraag, filetypes: set[File.Type]=None):
        for file in aanvraag.files.get_files():
            if filetypes is None or file.filetype in filetypes:
                self.files.sync(aanvraag.id, file)
    def read(self, id: int)->Aanvraag:
        aanvraag = super().read(id)
        aanvraag.files = self.files.find_all(aanvraag.id)
        return aanvraag
    def update(self, aanvraag: Aanvraag):
        self.__create_table_references(aanvraag)        
        super().update(aanvraag)
        self.sync_files(aanvraag)
    def delete(self, id: int):
        self.files.delete_all(id)
        super().delete(id)
    def read_all(self, filter_func = None)->list[Aanvraag]:
        if row:= self.database._execute_sql_command('select id from AANVRAGEN where status != ?', [Aanvraag.Status.DELETED], True):
            result = [self.read(r['id']) for r in row]
        else:
            result = []
        if result and filter_func:
            return list(filter(filter_func, result))
        else:
            return result
    def find_student_bedrijf(self, student: Student, bedrijf: Bedrijf)->list[Aanvraag]:
        return self.read_all(lambda a: a.student.stud_nr == student.stud_nr and a.bedrijf.id == bedrijf.id)
    def find_student(self, student: Student):
        result = []
        if (rows := self.database._execute_sql_command('select id from AANVRAGEN where stud_nr=?', [student.stud_nr], True)):
            for row in rows:
                result.append(self.read(row['id']))
        return result
    def __count_student_aanvragen(self, aanvraag: Aanvraag):
        if (row := self.database._execute_sql_command('select count(id) from AANVRAGEN where stud_nr=?', [aanvraag.student.stud_nr], True)):
            return row[0][0]
        else:
            return 0    
    def __create_table_references(self, aanvraag: Aanvraag):
        if (not self.bedrijven.read(aanvraag.bedrijf.id)) and \
            (row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [aanvraag.bedrijf.name], True)):
            aanvraag.bedrijf.id = row[0]['id']
        else:
            self.bedrijven.create(aanvraag.bedrijf)
        if not (self.studenten.read(aanvraag.student.stud_nr)):
            self.studenten.create(aanvraag.student)

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'
class ProcessLogStorage(ObjectStorage):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_process_log(database))
        self.process_log_aanvragen = CRUD_process_log_aanvragen(database)
        self.aanvragen = AanvraagStorage(database)
    def create(self, process_log: ProcessLog):
        super().create(process_log)
        self.process_log_aanvragen.create(process_log)
    def read(self, id: int)->ProcessLog:
        result: ProcessLog = super().read(id)
        self.__read_aanvragen(result)
        return result
    def update(self, process_log: ProcessLog):
        super().update(process_log)
        self.process_log_aanvragen.update(process_log)
    def delete(self, id: int):
        self.process_log_aanvragen.delete(id)
        super().delete(id)
    def delete_aanvraag(self, aanvraag_id: int):
        self.process_log_aanvragen.delete_aanvraag(aanvraag_id)
        super().delete(id)
    def find_log(self, id: int = EMPTY_ID)->ProcessLog:        
        if id == EMPTY_ID:
            if (row := self.database._execute_sql_command('select max(id) from PROCESSLOG where rolled_back = ? and action in (?,?,?)', 
                                                [0, ProcessLog.Action.CREATE, ProcessLog.Action.SCAN, ProcessLog.Action.MAIL], True)):
                id = row[0][0]
            if id is None or id == EMPTY_ID:
                log_warning(NoUNDOwarning)
                return None
        return self.read(id)
    def __read_aanvragen(self, process_log: ProcessLog):
        for record in self.process_log_aanvragen.read(process_log.id):
            process_log.add_aanvraag(self.aanvragen.read(record.aanvraag_id))

class AAPAStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self.aanvragen = AanvraagStorage(database)
        self.process_log = ProcessLogStorage(database)
    @property
    def files(self)->FilesStorage:
        return self.aanvragen.files
    @property
    def studenten(self)->StudentenStorage:
        return self.aanvragen.studenten
    def add_file_root(self, root: str, code = None):
        encoded_root = encode_path(root)
        code = add_root(encoded_root, code)
        if encoded_root != code: 
        #this means the root is already registered, re-encoding causes it to reduce to just the code
            create_root(self.database, code, encoded_root)
            self.commit()
    def commit(self):
        self.database.commit()