from data.AAPdatabase import AanvraagTableDefinition, BedrijfTableDefinition, FileTableDefinition, StudentTableDefinition, create_root
from data.classes import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, Bedrijf, FileInfo, FileInfos, FileType, StudentInfo
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops, SQLexpression as SQE
from general.keys import get_next_key
from data.roots import add_root, decode_path, encode_path
from general.log import logError, logInfo

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition())
    def __get_all_columns(self, include_key = True):
        result = ['id'] if include_key else []
        result.extend(['name'])
        return result
    def __get_all_values(self, bedrijf: Bedrijf, include_key = True):
        result = [bedrijf.id] if include_key else []
        result.extend([bedrijf.bedrijfsnaam])
        return result
    def create(self, bedrijf: Bedrijf):
        bedrijf.id = get_next_key(BedrijfTableDefinition.KEY_FOR_ID)
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(bedrijf))   
    def read(self, id: int)->Bedrijf:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return Bedrijf(row['name'], id)
        else:
            return None
    def update(self, bedrijf: Bedrijf):
        super().update(columns=self.__get_all_columns(False), values=self.__get_all_values(bedrijf, False), where=SQE('id', Ops.EQ, bedrijf.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FileTableDefinition())
    def __get_all_columns(self, include_key = True):
        result = ['filename'] if include_key else []        
        result.extend(['timestamp', 'digest', 'filetype', 'aanvraag_id'] )
        return result
    def __get_all_values(self, fileinfo: FileInfo, include_key = True):
        result = [encode_path(str(fileinfo.filename))] if include_key else []        
        result.extend([CRUD_files._timestamp_to_value(fileinfo.timestamp), fileinfo.digest, CRUD_files._filetype_to_value(fileinfo.filetype), fileinfo.aanvraag_id])
        return result
    def create(self, fileinfo: FileInfo):
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(fileinfo))   
    @staticmethod
    def _filename_to_value(filename: str):
        return f'{encode_path(filename)}'
    @staticmethod
    def _timestamp_to_value(timestamp):
        return FileInfo.timestamp_to_str(timestamp)
    @staticmethod
    def _filetype_to_value(filetype: FileType):
        return filetype.value
    def read(self, filename: str)->FileInfo:
        if row:=super().read(where=SQE('filename', Ops.EQ, CRUD_files._filename_to_value(filename), no_column_ref = True)):
            return FileInfo(decode_path(filename), timestamp=FileInfo.str_to_timestamp(row['timestamp']), digest = row['digest'], filetype=FileType(row['filetype']), aanvraag_id=row['aanvraag_id'])
        else:
            return None
    def read_all(self, filenames: list[str])->list[FileInfo]:
        if rows:=super().read(where=SQE('filename', Ops.IN, [CRUD_files._filename_to_value(filename) for filename in filenames], no_column_ref = True), multiple=True):
            result = []
            for row in rows:
                result.append(FileInfo(decode_path(row['filename']), timestamp=FileInfo.str_to_timestamp(row['timestamp']), digest = row['digest'], filetype=FileType(row['filetype']), aanvraag_id=row['aanvraag_id']))
            return result
        else:
            return None
    def update(self, fileinfo: FileInfo):
        super().update(columns=self.__get_all_columns(False), values=self.__get_all_values(fileinfo, False), 
            where=SQE('filename', Ops.EQ, CRUD_files._filename_to_value(fileinfo.filename), no_column_ref=True))
    def delete(self, filename: str):
        super().delete(where=SQE('filename', Ops.EQ, CRUD_files._filename_to_value(filename), no_column_ref=True))

class CRUD_studenten(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentTableDefinition())
    def __get_all_columns(self, include_key = True):        
        result = ['stud_nr'] if include_key else []
        result.extend(['full_name', 'first_name', 'email', 'tel_nr'])
        return result
    def __get_all_values(self, studInfo: StudentInfo, include_key = True):
        result = [studInfo.studnr] if include_key else []
        result.extend([studInfo.student_name, studInfo.first_name, studInfo.email, studInfo.telno])
        return result
    def create(self, studInfo: StudentInfo):
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(studInfo))   
    def read(self, studnr: str)->StudentInfo:
        if row:=super().read(where=SQE('stud_nr', Ops.EQ, studnr)):
            return StudentInfo(student_name=row['full_name'], studnr=studnr, telno=row['tel_nr'], email=row['email']) 
        else:
            return None
    def update(self, studInfo: StudentInfo):
        super().update(columns=self.__get_all_columns(False), values=self.__get_all_values(studInfo, False), where=SQE('stud_nr', Ops.EQ, studInfo.studnr))
    def delete(self, studnr: str):
        super().delete(where=SQE('stud_nr', Ops.EQ, studnr))

class CRUD_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition())
    def __get_all_columns(self, include_key = True):
        result = ['id'] if include_key else []
        result.extend(['stud_nr', 'bedrijf_id', 'datum_str', 'titel', 'aanvraag_nr', 'beoordeling', 'status'])
        return result
    @staticmethod
    def __beoordeling_to_value(beoordeling: AanvraagBeoordeling):
        return beoordeling.value
    @staticmethod
    def __status_to_value(status: AanvraagStatus):
        return status.value
    def __get_all_values(self, docInfo: AanvraagInfo, include_key = True):
        result = [docInfo.id] if include_key else []
        result.extend([docInfo.student.studnr, docInfo.bedrijf.id, docInfo.datum_str, docInfo.titel, docInfo.aanvraag_nr, CRUD_aanvragen.__beoordeling_to_value(docInfo.beoordeling), CRUD_aanvragen.__status_to_value(docInfo.status)])
        return result
    def create(self, docInfo: AanvraagInfo):
        docInfo.id = get_next_key(AanvraagTableDefinition.KEY_FOR_ID)
        super().create(columns=self.__get_all_columns(False), values=self.__get_all_values(docInfo, False))
    def __build_aanvraag(self, row)->AanvraagInfo:
        student = CRUD_studenten(self.database).read(row['stud_nr'])
        bedrijf = CRUD_bedrijven(self.database).read(row['bedrijf_id'])
        result =  AanvraagInfo(student, bedrijf=bedrijf, datum_str=row['datum_str'], titel=row['titel'],beoordeling=AanvraagBeoordeling(row['beoordeling']), status=AanvraagStatus(row['status']), id=row['id'], aanvraag_nr=row['aanvraag_nr'])
        return result
    def read(self, id: int)->AanvraagInfo:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return self.__build_aanvraag(row)
        else:
            return None
    def update(self, docInfo: AanvraagInfo):
        super().update(columns=self.__get_all_columns(False), 
                    values=self.__get_all_values(docInfo, False), where=SQE('id', Ops.EQ, docInfo.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))

class FileInfoStorage:
    def __init__(self, database: Database):
        self.database: Database = database
        self.crud_files = CRUD_files(database)
    def find(self, aanvraag_id: int, filetype: FileType)->FileInfo:
        if row:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype=?', 
                [aanvraag_id, CRUD_files._filetype_to_value(filetype)], True):
            info = self.crud_files.read(row[0]["filename"])
            logInfo(f'success: {info}')
            return info
        return None
    def __load(self, aanvraag_id: int, filetypes: list[FileType])->list[FileInfo]:
        params = [aanvraag_id]
        params.extend([CRUD_files._filetype_to_value(ft) for ft in filetypes])
        if rows:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype in (' + ','.join('?'*len(filetypes))+')', params, True):
            filenames=[]
            filenames.extend([row["filename"] for row in rows])
            result = self.crud_files.read_all(filenames)
            logInfo(f'success: {[str(info) for info in result]}')
            return result
        return None
    def find_all(self, aanvraag_id: int)->FileInfos:
        result = FileInfos(aanvraag_id)
        filetypes = []
        for ft in FileType:
            if ft == FileType.UNKNOWN:
                continue
            filetypes.append(ft)
            result.reset_info(ft)
        for fileinfo in self.__load(aanvraag_id, filetypes):
            if fileinfo:
                result.set_info(fileinfo)
        return result        
    def find_all_for_filetype(self, filetype: FileType)->list[FileInfo]:
        result = []
        for row in self.database._execute_sql_command('select filename from FILES where filetype=?', [CRUD_files._filetype_to_value(filetype)], True):
            result.append(self.crud_files.read(row['filename']))
        return result
    def find_digest(self, digest)->FileInfo:
        if row:= self.database._execute_sql_command('select filename from FILES where digest=?', [digest], True):
            info = self.crud_files.read(row[0]["filename"])
            logInfo(f'success: {info}')
            return info

    def replace(self, aanvraag_id, info: FileInfo):
        info.aanvraag_id = aanvraag_id
        if (cur_info:=self.find(aanvraag_id, info.filetype)) is not None:
            if info.filename:
                self.crud_files.update(info)
            else:
                self.crud_files.delete(cur_info.filename)
        else:
            self.crud_files.create(info)
    def delete(self, aanvraag_id):
        for info in self.__load(aanvraag_id, [ft for ft in FileType if ft != FileType.UNKNOWN]):
            self.crud_files.delete(info.filename)


class BedrijvenStorage:
    def __init__(self, database: Database):
        self.database: Database = database
        self.crud_bedrijven = CRUD_bedrijven(database)
    def create(self, bedrijf: Bedrijf):
        if row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [bedrijf.bedrijfsnaam], True):
            bedrijf.id = row[0]['id']
        else:
            self.crud_bedrijven.create(bedrijf)
    def read(self, id: int)->Bedrijf:
        return self.crud_bedrijven.read(id)
    def update(self, bedrijf: Bedrijf):
        self.crud_bedrijven.update(bedrijf)
    def delete(self, id: int):
        self.crud_bedrijven.delete(id)

class StudentenStorage:
    def __init__(self, database: Database):
        self.database: Database = database
        self.crud_studenten = CRUD_studenten(database)
    def create(self, student: StudentInfo):
        self.crud_studenten.create(student)
    def read(self, studnr: str)->StudentInfo:
        return self.crud_studenten.read(studnr)
    def update(self, student: StudentInfo):
        self.crud_studenten.update(student)
    def delete(self, studnr: str):
        self.crud_studenten.delete(studnr)


class AanvraagStorage:
    def __init__(self, database: Database):
        self.database: Database = database
        self.file_info = FileInfoStorage(database)
        self.bedrijven = BedrijvenStorage(database)
        self.studenten = StudentenStorage(database)
        self.crud_aanvragen = CRUD_aanvragen(database)
    def create(self, aanvraag: AanvraagInfo, source_file: FileInfo):
        self.__create_references(aanvraag)
        aanvraag.files.set_info(source_file)
        aanvraag.aanvraag_nr = self.__count_student_aanvragen(aanvraag) + 1
        self.crud_aanvragen.create(aanvraag)
        self.__create_sourcefile(aanvraag.id, source_file)
    def read(self, id: int)->AanvraagInfo:
        aanvraag = self.crud_aanvragen.read(id)
        aanvraag.files = self.file_info.find_all(aanvraag.id)
        return aanvraag
    def update(self, aanvraag: AanvraagInfo):
        self.__create_references(aanvraag)        
        self.crud_aanvragen.update(aanvraag)
        for info in aanvraag.files:
            self.file_info.replace(aanvraag.id, info)
    def delete(self, id: int):
        self.file_info.delete(id)
        self.crud_aanvragen.delete(id)
    def find_student_bedrijf(self, student: StudentInfo, bedrijf: Bedrijf)->list[AanvraagInfo]:
        return self.crudread_aanvragen(lambda a: a.student.studnr == student.studnr and a.bedrijf.id == bedrijf.id)

    def __count_student_aanvragen(self, aanvraag: AanvraagInfo):
        if (row := self.database._execute_sql_command('select count(id) from AANVRAGEN where stud_nr=?', [aanvraag.student.studnr], True)):
            return row[0][0]
        else:
            return 0    
    def __create_references(self, aanvraag: AanvraagInfo):
        if (not self.bedrijven.read(aanvraag.bedrijf.id)) and \
            (row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [aanvraag.bedrijf.bedrijfsnaam], True)):
            aanvraag.bedrijf.id = row[0]['id']
        else:
            self.bedrijven.create(aanvraag.bedrijf)
        if not (self.studenten.read(aanvraag.student.studnr)):
            self.studenten.create(aanvraag.student)
    def __create_sourcefile(self, aanvraag_id,  source_file: FileInfo):
        self.file_info.replace(aanvraag_id, source_file)
    def read_all(self, filter_func = None)->list[AanvraagInfo]:
        if row:= self.database._execute_sql_command('select id from AANVRAGEN', [], True):
            result = [self.read(r['id']) for r in row]
        else:
            result = []
        if result and filter_func:
            return list(filter(filter_func, result))
        else:
            return result
    def find_aanvragen_for_student_bedrijf(self, student: StudentInfo, bedrijf: Bedrijf)->list[AanvraagInfo]:
        return self.read_all(lambda a: a.student.studnr == student.studnr and a.bedrijf.id == bedrijf.id)
    def find_aanvragen_for_student(self, student: StudentInfo):
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

class AAPStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self.aanvragen = AanvraagStorage(database)
    @property
    def file_info(self)->FileInfoStorage:
        return self.aanvragen.file_info
        # self.crud_files = CRUD_files(database)
        # self.crud_studenten = CRUD_studenten(database)
        # self.crud_aanvragen = CRUD_aanvragen(database)


    # def create_fileinfo(self, fileinfo: FileInfo):
    #     self.crud_files.create(fileinfo)
    # def read_fileinfo(self, filename: str)->FileInfo:
    #     return self.crud_files.read(filename)
    # def update_fileinfo(self, fileinfo: FileInfo):
    #     self.crud_files.update(fileinfo)
    # def delete_fileinfo(self, filename: str):
    #     self.crud_files.delete(filename)
    def add_file_root(self, root: str, code = None):
        encoded_root = encode_path(root)
        code = add_root(encoded_root, code)
        if encoded_root != code: 
        #this means the root is already registered, re-encoding causes it to reduced to just the code
            create_root(self.database, code, encoded_root)
            self.commit()

    # def __create_aanvraag_references(self, aanvraag: AanvraagInfo):
    #     if (not self.read_bedrijf(aanvraag.bedrijf.id)) and (row:= self.database._execute_sql_command('select * from BEDRIJVEN where (name=?)', [aanvraag.bedrijf.bedrijfsnaam], True)):
    #         aanvraag.bedrijf.id = row[0]['id']
    #     else:
    #         self.create_bedrijf(aanvraag.bedrijf)
    #     if not (student := self.read_student(aanvraag.student.studnr)):
    #         self.create_student(aanvraag.student)
    # def __create_sourcefile(self, aanvraag_id,  source_file: FileInfo):
    #     self.replace_fileinfo(aanvraag_id, source_file)
    #     # source_file.aanvraag_id = aanvraag_id
    #     # if (self.read_fileinfo(source_file.filename)):
    #     #     self.update_fileinfo(source_file)
    #     # else:
    #     #     self.create_fileinfo(source_file)

    # def create_aanvraag(self, aanvraag: AanvraagInfo, source_file: FileInfo):
    #     self.__create_aanvraag_references(aanvraag)
    #     aanvraag.files.set_info(source_file)
    #     aanvraag.aanvraag_nr = self.__count_student_aanvragen(aanvraag) + 1
    #     self.crud_aanvragen.create(aanvraag)
    #     self.__create_sourcefile(aanvraag.id, source_file)
    # def read_aanvraag(self, id: int)->AanvraagInfo:
    #     aanvraag = self.crud_aanvragen.read(id)
    #     aanvraag.files = self.find_fileinfos(aanvraag.id)
    #     return aanvraag
    # def update_aanvraag(self, aanvraag: AanvraagInfo):
    #     self.crud_aanvragen.update(aanvraag)
    # def delete_aanvraag(self, id: int):
    #     self.crud_aanvragen.delete(id)
    # def read_aanvragen(self, filter_func = None)->list[AanvraagInfo]:
    #     if row:= self.database._execute_sql_command('select id from AANVRAGEN', [], True):
    #         result = [self.aanvragen.read(r['id']) for r in row]
    #     else:
    #         result = []
    #     if result and filter_func:
    #         return list(filter(filter_func, result))
    #     else:
    #         return result
    # def find_fileinfo(self, aanvraag_id: int, filetype: FileType)->FileInfo:
    #     if row:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype=?', 
    #             [aanvraag_id, CRUD_files._filetype_to_value(filetype)], True):
    #         info = self.crud_files.read(row[0]["filename"])
    #         logInfo(f'success: {info}')
    #         return info
    #     return None
    # def __load_fileinfos(self, aanvraag_id: int, filetypes: list[FileType])->list[FileInfo]:
    #     params = [aanvraag_id]
    #     params.extend([CRUD_files._filetype_to_value(ft) for ft in filetypes])
    #     if rows:= self.database._execute_sql_command('select filename from FILES where aanvraag_id=? and filetype in (' + ','.join('?'*len(filetypes))+')', params, True):
    #         filenames=[]
    #         filenames.extend([row["filename"] for row in rows])
    #         result = self.crud_files.read_all(filenames)
    #         logInfo(f'success: {[str(info) for info in result]}')
    #         return result
    #     return None
    # def find_fileinfos(self, aanvraag_id: int)->FileInfos:
    #     result = FileInfos(aanvraag_id)
    #     filetypes = []
    #     for ft in FileType:
    #         if ft == FileType.UNKNOWN:
    #             continue
    #         filetypes.append(ft)
    #         result.reset_info(ft)
    #     for fileinfo in self.__load_fileinfos(aanvraag_id, filetypes):
    #         if fileinfo:
    #             result.set_info(fileinfo)
    #     return result        
    # def find_fileinfos_for_filetype(self, filetype)->list[FileInfo]:
    #     result = []
    #     for row in self.database._execute_sql_command('select filename from FILES where filetype=?', [CRUD_files._filetype_to_value(filetype)], True):
    #         result.append(self.file_info.read(row['filename']))
    #     return result
    # def replace_fileinfo(self, aanvraag_id, info: FileInfo):
    #     info.aanvraag_id = aanvraag_id
    #     if (cur_info:=self.find_fileinfo(aanvraag_id, info.filetype)) is not None:
    #         if info.filename:
    #             self.update_fileinfo(info)
    #         else:
    #             self.delete_fileinfo(cur_info.filename)
    #     else:
    #         self.create_fileinfo(info)
    # def find_fileinfo_for_digest(self, digest)->FileInfo:
    #     if row:= self.database._execute_sql_command('select filename from FILES where digest=?', [digest], True):
    #         info = self.crud_files.read(row[0]["filename"])
    #         logInfo(f'success: {info}')
    #         return info
    # def find_all_fileinfos(self):
    #     result = []
    #     for row in self.database._execute_sql_command('select filename from FILES', [], True):
    #         info = self.read_fileinfo(decode_path(row['filename']))
    #         if not info:
    #             logError(f"problem with reading filename: {row['filename']}")
    #         else:
    #             result.append(info)
    #     return result
    # def find_aanvragen(self, student: StudentInfo, bedrijf: Bedrijf)->list[AanvraagInfo]:
    #     return self.read_aanvragen(lambda a: a.student.studnr == student.studnr and a.bedrijf.id == bedrijf.id)
    # def find_aanvragen_for_student(self, student: StudentInfo):
    #     result = []
    #     if (rows := self.database._execute_sql_command('select id from AANVRAGEN where stud_nr=?', [student.studnr], True)):
    #         for row in rows:
    #             result.append(self.read_aanvraag(row['id']))
    #     return result
    # def max_aanvraag_id(self):
    #     if (row := self.database._execute_sql_command('select max(id) from AANVRAGEN', [], True)) and row[0][0]:
    #         return row[0][0]           
    #     else:
    #         return 0                    
    def commit(self):
        self.database.commit()
    

