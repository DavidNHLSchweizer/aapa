from data.AAPdatabase import AanvraagTableDefinition, BedrijfTableDefinition, FileTableDefinition, StudentTableDefinition
from data.aanvraag_info import AanvraagDocumentInfo, AanvraagInfo, Bedrijf, FileInfo, FileType, StudentInfo
from database.SQL import SQLselect
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops, SQLexpression as SQE

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition())
    def __get_all_columns(self):
        return ['name']
    def __get_all_values(self, bedrijf: Bedrijf):
        return [bedrijf.bedrijfsnaam]    
    def create(self, bedrijf: Bedrijf):
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(bedrijf))   
    def read(self, id: int)->Bedrijf:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return Bedrijf(row['name'], id)
        else:
            return None
    def update(self, bedrijf: Bedrijf):
        super().update(columns=self.__get_all_columns(), values=self.__get_all_values(bedrijf), where=SQE('id', Ops.EQ, bedrijf.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FileTableDefinition())
    def __get_all_columns(self, include_key = True):
        COLS = ['filename', 'timestamp', 'filetype'] 
        if include_key: 
            return COLS
        else:
            return COLS[1:]
    def __get_all_values(self, fileinfo: FileInfo, include_key = True):
        if include_key:
            result = [str(fileinfo.filename)]
        else:
            result = []
        result.extend([CRUD_files.__timestamp_to_value(fileinfo.timestamp), CRUD_files.__filetype_to_value(fileinfo.filetype)])
        return result
    def create(self, fileinfo: FileInfo):
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(fileinfo))   
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
        super().update(columns=self.__get_all_columns(false), values=self.__get_all_values(fileinfo, False), 
        where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(fileinfo.filename)))
    def delete(self, filename: str):
        super().delete(where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(filename)))

class CRUD_studenten(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentTableDefinition())
    def __get_all_columns(self, include_key = True):
        COLS= ['stud_nr', 'full_name', 'first_name', 'email', 'tel_nr']
        if include_key:
            return COLS
        else:
            return COLS[1:]
    def __get_all_values(self, studInfo: StudentInfo, include_key = True):
        if include_key:
            result = [studInfo.studnr]
        else:
            result = []
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
    def __get_all_columns(self):
        return ['filename', 'stud_nr', 'bedrijf_id', 'datum_str', 'titel', 'beoordeling']
    def __get_all_values(self, docInfo: AanvraagDocumentInfo):
        return [str(docInfo.fileinfo.filename),  docInfo.student.studnr, docInfo.bedrijf.id, docInfo.datum_str, docInfo.titel, docInfo.beoordeling]
    def create(self, docInfo: AanvraagDocumentInfo):
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(docInfo))   
    def __build_aanvraag(self, row)->AanvraagDocumentInfo:
        fileinfo = CRUD_files(self.database).read(row['filename'])
        student = CRUD_studenten(self.database).read(row['stud_nr'])
        bedrijf = CRUD_bedrijven(self.database).read(row['bedrijf_id'])
        return AanvraagDocumentInfo(fileinfo, student, bedrijf,  row['datum_str'], row['titel'], beoordeling=row['beoordeling'])
    def read(self, id: int)->AanvraagDocumentInfo:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return self.__build_aanvraag(row)
        else:
            return None
    def update(self, docInfo: AanvraagDocumentInfo):
        super().update(columns=self.__get_all_columns(), 

HM: DOCINFO heeft geen ID!
                    values=self.__get_all_values(docInfo), where=SQE('id', Ops.EQ, docInfo.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))

