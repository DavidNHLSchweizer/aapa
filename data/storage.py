from data.AAPdatabase import  create_root
from data.classes import AUTODIGEST, AUTOTIMESTAMP, AanvraagInfo, Bedrijf, FileInfo, FileInfos, FileType, StudentInfo
from data.tables.aanvragen import CRUD_aanvragen
from data.tables.bedrijven import  CRUD_bedrijven
from data.tables.files import CRUD_files
from data.tables.studenten import CRUD_studenten
from database.crud import CRUDbase
from database.database import Database
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
from data.roots import add_root, encode_path
from general.log import log_info, log_warning

AAPAClass = type[Bedrijf|StudentInfo|FileInfo|FileInfos|AanvraagInfo]
KeyClass = type[int|str]
class StorageBase:
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
        
class BedrijvenStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_bedrijven(database))
    def create(self, bedrijf: Bedrijf):
        if row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [bedrijf.bedrijfsnaam], True):
            bedrijf.id = row[0]['id']
        else:
            super().create(bedrijf)

class StudentenStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_studenten(database))

class FileInfoStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_files(database))
    def find(self, aanvraag_id: int, filetype: FileType)->FileInfo:
        if row:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype=?', 
                [aanvraag_id, CRUD_files._filetype_to_value(filetype)], True):
            info = self.read(row[0]["filename"])
            log_info(f'success: {info}')
            return info
        return None
    @property
    def crud_files(self)->CRUD_files:
        return self.crud
    def __load(self, aanvraag_id: int, filetypes: set[FileType])->list[FileInfo]:
        params = [aanvraag_id]
        params.extend([CRUD_files._filetype_to_value(ft) for ft in filetypes])
        if rows:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype in (' + ','.join('?'*len(filetypes))+')', params, True):
            filenames=[]
            filenames.extend([row["filename"] for row in rows])
            result = self.crud_files.read_all(filenames)
            log_info(f'success: {[str(info) for info in result]}')
            return result
        return None
    def find_all(self, aanvraag_id: int)->FileInfos:
        result = FileInfos(aanvraag_id)
        filetypes = {ft for ft in FileType if ft != FileType.UNKNOWN}
        result.reset_info(filetypes)
        for fileinfo in self.__load(aanvraag_id, filetypes):
            if fileinfo:
                result.set_info(fileinfo)
        return result        
    def find_all_for_filetype(self, filetypes: FileType | set[FileType])->list[FileInfo]:
        if isinstance(filetypes, set):
            place_holders = f' in ({",".join("?"*len(filetypes))})' 
            params = [CRUD_files._filetype_to_value(ft) for ft in filetypes]
        else:
            place_holders = '=?'
            params = [CRUD_files._filetype_to_value(filetypes)]
        result = []
        for row in self.database._execute_sql_command('select filename from FILES where filetype' + place_holders, params, True):
            result.append(self.read(row['filename']))
        return result
    def find_digest(self, digest)->FileInfo:
        if row:= self.database._execute_sql_command('select filename from FILES where digest=?', [digest], True):
            info = self.read(row[0]["filename"])
            log_info(f'success: {info}')
            return info
    def sync(self, aanvraag_id, info: FileInfo):
        info.aanvraag_id = aanvraag_id
        if (cur_info:=self.find(aanvraag_id, info.filetype)) is not None:
            #file currently exists in database
            if info.filename:
                self.update(info)
            else:
                self.delete(cur_info.filename)
        elif info.filename:            
            if (cur_info := self.read(info.filename)):
                #file is known in database, PROBABLY (!?) not linked to aanvraag 
                log_warning(f'bestand {summary_string(info.filename, maxlen=80)} is bekend in database:\n\t{cur_info.summary()}.\nWordt vervangen door\n\t{info.summary()}')
                self.update(info)
            else:
                #new file
                self.create(info)
    def delete_all(self, aanvraag_id):
        for info in self.__load(aanvraag_id, {ft for ft in FileType if ft != FileType.UNKNOWN}):
            self.delete(info.filename)
    def is_duplicate(self, file: FileInfo):
        return (stored:=self.read(file.filename)) is not None and stored.digest == file.digest
    def known_file(self, filename: str)->FileInfo:
        return self.find_digest(FileInfo.get_digest(filename))
    def store_invalid(self, filename):
        if (stored:=self.read(filename)):
            stored.filetype = FileType.INVALID_PDF
            stored.aanvraag_id=EMPTY_ID
            self.update(stored)
        else:
            self.create(FileInfo(filename, timestamp=AUTOTIMESTAMP, digest=AUTODIGEST, filetype=FileType.INVALID_PDF, aanvraag_id=EMPTY_ID))
        self.database.commit()
    def is_known_invalid(self, filename):
        if (stored:=self.read(filename)):
            return stored.filetype == FileType.INVALID_PDF
        else:
            return False     

class AanvraagStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, CRUD_aanvragen(database))
        self.file_info = FileInfoStorage(database)
        self.bedrijven = BedrijvenStorage(database)
        self.studenten = StudentenStorage(database)
    def create(self, aanvraag: AanvraagInfo):#, source_file: FileInfo):
        self.__create_table_references(aanvraag)
        # aanvraag.files.set_info(source_file)
        aanvraag.aanvraag_nr = self.__count_student_aanvragen(aanvraag) + 1
        super().create(aanvraag)
        self.sync_files(aanvraag, {FileType.AANVRAAG_PDF})
    def sync_files(self, aanvraag: AanvraagInfo, filetypes: set[FileType]=None):
        for info in aanvraag.files.get_infos():
            if filetypes is None or info.filetype in filetypes:
                self.file_info.sync(aanvraag.id, info)
    def read(self, id: int)->AanvraagInfo:
        aanvraag = super().read(id)
        aanvraag.files = self.file_info.find_all(aanvraag.id)
        return aanvraag
    def update(self, aanvraag: AanvraagInfo):
        self.__create_table_references(aanvraag)        
        super().update(aanvraag)
        self.sync_files(aanvraag)
    def delete(self, id: int):
        self.file_info.delete_all(id)
        super().delete(id)
    def read_all(self, filter_func = None)->list[AanvraagInfo]:
        if row:= self.database._execute_sql_command('select id from AANVRAGEN', [], True):
            result = [self.read(r['id']) for r in row]
        else:
            result = []
        if result and filter_func:
            return list(filter(filter_func, result))
        else:
            return result
    def find_student_bedrijf(self, student: StudentInfo, bedrijf: Bedrijf)->list[AanvraagInfo]:
        return self.read_all(lambda a: a.student.studnr == student.studnr and a.bedrijf.id == bedrijf.id)
    def find_student(self, student: StudentInfo):
        result = []
        if (rows := self.database._execute_sql_command('select id from AANVRAGEN where stud_nr=?', [student.studnr], True)):
            for row in rows:
                result.append(self.read(row['id']))
        return result
    def max_id(self):
        if (row := self.database._execute_sql_command('select max(id) from AANVRAGEN', [], True)) and row[0][0]:
            return row[0][0]           
        else:
            return 0                    
    def __count_student_aanvragen(self, aanvraag: AanvraagInfo):
        if (row := self.database._execute_sql_command('select count(id) from AANVRAGEN where stud_nr=?', [aanvraag.student.studnr], True)):
            return row[0][0]
        else:
            return 0    
    def __create_table_references(self, aanvraag: AanvraagInfo):
        if (not self.bedrijven.read(aanvraag.bedrijf.id)) and \
            (row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [aanvraag.bedrijf.bedrijfsnaam], True)):
            aanvraag.bedrijf.id = row[0]['id']
        else:
            self.bedrijven.create(aanvraag.bedrijf)
        if not (self.studenten.read(aanvraag.student.studnr)):
            self.studenten.create(aanvraag.student)

class AAPStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self.aanvragen = AanvraagStorage(database)
    @property
    def file_info(self)->FileInfoStorage:
        return self.aanvragen.file_info
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