from data.AAPdatabase import AanvraagTableDefinition, BedrijfTableDefinition, FileTableDefinition, StudentTableDefinition
from data.aanvraag_info import AanvraagBeoordeling, AanvraagDocumentInfo, AanvraagInfo, AanvraagStatus, Bedrijf, FileInfo, FileType, StudentInfo
from database.SQL import SQLselect
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops, SQLexpression as SQE
from database.tabledef import TableDefinition
from general.keys import get_next_key

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
        result.extend(['timestamp', 'filetype'] )
        return result
    def __get_all_values(self, fileinfo: FileInfo, include_key = True):
        result = [str(fileinfo.filename)] if include_key else []        
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
            return FileInfo(filename, FileInfo.str_to_timestamp(row['timestamp']), FileType(row['filetype']))
        else:
            return None
    def update(self, fileinfo: FileInfo):
        super().update(columns=self.__get_all_columns(False), values=self.__get_all_values(fileinfo, False), 
            where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(fileinfo.filename), no_column_ref=True))
    def delete(self, filename: str):
        super().delete(where=SQE('filename', Ops.EQ, CRUD_files.__filename_to_value(filename), no_column_ref=True))

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
        result.extend(['filename', 'stud_nr', 'bedrijf_id', 'datum_str', 'titel', 'beoordeling', 'status'])
        return result
    @staticmethod
    def __beoordeling_to_value(beoordeling: AanvraagBeoordeling):
        return beoordeling.value
    @staticmethod
    def __status_to_value(status: AanvraagStatus):
        return status.value
    def __get_all_values(self, docInfo: AanvraagDocumentInfo, include_key = True):
        result = [docInfo.id] if include_key else []
        result.extend([str(docInfo.fileinfo.filename),  docInfo.student.studnr, docInfo.bedrijf.id, docInfo.datum_str, docInfo.titel, CRUD_aanvragen.__beoordeling_to_value(docInfo.beoordeling), CRUD_aanvragen.__status_to_value(docInfo.status)])
        return result
    def create(self, docInfo: AanvraagDocumentInfo):
        docInfo.id = get_next_key(AanvraagTableDefinition.KEY_FOR_ID)
        super().create(columns=self.__get_all_columns(False), values=self.__get_all_values(docInfo, False))
    def __build_aanvraag(self, row)->AanvraagDocumentInfo:
        fileinfo = CRUD_files(self.database).read(row['filename'])
        student = CRUD_studenten(self.database).read(row['stud_nr'])
        bedrijf = CRUD_bedrijven(self.database).read(row['bedrijf_id'])
        result =  AanvraagDocumentInfo(fileinfo, student, bedrijf,  row['datum_str'], row['titel'], AanvraagBeoordeling(row['beoordeling']), AanvraagStatus(row['status']), id=row['id'])
        return result
    def read(self, id: int)->AanvraagDocumentInfo:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return self.__build_aanvraag(row)
        else:
            return None
    def update(self, docInfo: AanvraagDocumentInfo):
        super().update(columns=self.__get_all_columns(False), 
                    values=self.__get_all_values(docInfo, False), where=SQE('id', Ops.EQ, docInfo.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))

