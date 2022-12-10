from data.AAPdatabase import AanvraagTableDefinition, BedrijfTableDefinition, FileTableDefinition, StudentTableDefinition
from data.aanvraag_info import AanvraagInfo, Bedrijf, FileInfo, FileType, StudentInfo
from database.SQL import SQLselect
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops, SQLexpression as SQE

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition())
    def __get_create_columns(self):
        return ['name']
    def __get_create_values(self, bedrijf: Bedrijf):
        return [bedrijf.bedrijfsnaam]    
    def create(self, bedrijf: Bedrijf):
        super().create(columns=self.__get_create_columns(), values=self.__get_create_values(bedrijf))   
    def read(self, id: int)->Bedrijf:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return Bedrijf(row['name'], id)
        else:
            return None
    def update(self, bedrijf: Bedrijf):
        super().update(columns=['name'], values=[bedrijf.bedrijfsnaam], where=SQE('id', Ops.EQ, bedrijf.id))
    def delete(self, bedrijf: Bedrijf):
        super().delete(where=SQE('id', Ops.EQ, bedrijf.id))

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FileTableDefinition())
    def __get_create_columns(self):
        return ['filename', 'timestamp', 'filetype']
    def __get_create_values(self, fileinfo: FileInfo):
        return [str(fileinfo.filename), CRUD_files.__timestamp_to_value(fileinfo.timestamp), CRUD_files.__filetype_to_value(fileinfo.filetype)]
    def create(self, fileinfo: FileInfo):
        super().create(columns=self.__get_create_columns(), values=self.__get_create_values(fileinfo))   
    @staticmethod
    def __filename_to_value(filename: str):
        return f'{filename}'
    @staticmethod
    def __timestamp_to_value(timestamp):
        return FileInfo.timestamp_to_str(timestamp)
    @staticmethod
    def __filetype_to_value(filetype: FileType):
        return filetype.value
    def read(self, filename: str)->FileInfo:
        if row:=super().read(where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(filename), no_column_ref = True)):
            return FileInfo(filename, FileInfo.str_to_timestamp(row['timestamp']), row['filetype'])
        else:
            return None
    def update(self, fileinfo: FileInfo):
        super().update(columns=['timestamp', 'filetype'], values=[CRUD_files.__timestamp_to_value(fileinfo.timestamp), fileinfo.filetype], where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(fileinfo.filename)))
    def delete(self, fileinfo: FileInfo):
        super().delete(where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(fileinfo.filename)))

class CRUD_studenten(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentTableDefinition())
    def __get_create_columns(self):
        return ['stud_nr', 'full_name', 'first_name', 'email', 'tel_nr']
    def __get_create_values(self, studInfo: StudentInfo):
        return [studInfo.studnr, studInfo.student_name, studInfo.first_name, studInfo.email, studInfo.telno]
    def create(self, studInfo: StudentInfo):
        super().create(columns=self.__get_create_columns(), values=self.__get_create_values(studInfo))   
    def read(self, studnr: str)->StudentInfo:
        if row:=super().read(where=SQE('stud_nr', Ops.EQ, studnr)):
            return StudentInfo(student_name=row['full_name'], studnr=studnr, telno=row['telno'], email=row['email'])
        else:
            return None
    def update(self, studInfo: StudentInfo):
        super().update(columns=['full_name', 'first_name', 'email', 'tel_nr'], values=[studInfo.student_name, studInfo.first_name, studInfo.email, studInfo.telno], where=SQE('stud_nr', Ops.EQ, studInfo.studnr))
    def delete(self, studInfo: StudentInfo):
        super().delete(where=SQE('stud_nr', Ops.EQ, studInfo.studnr))



# class AanvraagTableDefinition(TableDefinition):
#     def __init__(self):
#         super().__init__('AANVRAGEN', autoid = True)
#         self.add_column('filename', dbc.TEXT)
#         self.add_column('title', dbc.TEXT)
#         self.add_column('stud_nr', dbc.TEXT)
#         self.add_column('bedrijf_id', dbc.INTEGER)
#         self.add_column('grade', dbc.INTEGER)


# class CRUD_aanvragen(CRUDbase):
#     def __init__(self, database: Database):
#         super().__init__(database, AanvraagTableDefinition())
#     def __get_create_columns(self):
#         return ['filename', 'title', 'stud_nr', 'bedrijf_id', 'grade']
#     def __get_create_values(self, docInfo: AanvraagInfo):
#         return [str(docInfo.filename), docInfo.title, CRUD_files.__filetype_to_value(fileinfo.filetype)]
#     def create(self, fileinfo: FileInfo):
#         super().create(columns=self.__get_create_columns(), values=self.__get_create_values(fileinfo))   
#     @staticmethod
#     def __filename_to_value(filename):
#         return f"'{filename}'"
#     @staticmethod
#     def __timestamp_to_value(timestamp):
#         return FileInfo.timestamp_to_str(timestamp)
#     @staticmethod
#     def __filetype_to_value(filetype: FileType):
#         return filetype.value
#     def read(self, filename: str)->FileInfo:
#         if row:=super().read(where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(filename))):
#             return FileInfo(filename, FileInfo.str_to_timestamp(row['timestamp']), row['filetype'])
#         else:
#             return None
#     def update(self, fileinfo: FileInfo):
#         super().update(columns=['timestamp', 'filetype'], values=[CRUD_files.__timestamp_to_value(fileinfo.timestamp), fileinfo.filetype], where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(fileinfo.filename)))
#     def delete(self, fileinfo: FileInfo):
#         super().delete(where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(fileinfo.filename)))

