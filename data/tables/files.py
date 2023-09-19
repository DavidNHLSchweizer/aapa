from data.roots import decode_path, encode_path
from database.dbConst import EMPTY_ID
from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import FileTableDefinition
from data.classes import AUTODIGEST, TSC, FileInfo, FileType
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops
from general.fileutil import summary_string
from general.log import log_info, log_warning

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FileTableDefinition())
    def __get_all_columns(self, include_key = True):
        result = ['filename'] if include_key else []        
        result.extend(['timestamp', 'digest', 'filetype', 'aanvraag_id'] )
        return result
    def __get_all_values(self, fileinfo: FileInfo, include_key = True):
        result = [encode_path(str(fileinfo.filename))] if include_key else []        
        result.extend([TSC.timestamp_to_str(fileinfo.timestamp), fileinfo.digest, CRUD_files._filetype_to_value(fileinfo.filetype), fileinfo.aanvraag_id])
        return result
    def create(self, fileinfo: FileInfo):
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(fileinfo))   
    @staticmethod
    def _filename_to_value(filename: str):
        return f'{encode_path(filename)}'
    # @staticmethod
    # def _timestamp_to_value(timestamp):
    #     return TSC.timestamp_to_str(timestamp)
    @staticmethod
    def _filetype_to_value(filetype: FileType):
        return filetype.value
    def read(self, filename: str)->FileInfo:
        if row:=super().read(where=SQE('filename', Ops.EQ, CRUD_files._filename_to_value(filename), no_column_ref = True)):
            return FileInfo(decode_path(filename), timestamp=TSC.str_to_timestamp(row['timestamp']), digest = row['digest'], filetype=FileType(row['filetype']), aanvraag_id=row['aanvraag_id'])
        else:
            return None
    def read_all(self, filenames: list[str])->list[FileInfo]:
        if rows:=super().read(where=SQE('filename', Ops.IN, [CRUD_files._filename_to_value(filename) for filename in filenames], no_column_ref = True), multiple=True):
            result = []
            for row in rows:
                result.append(FileInfo(decode_path(row['filename']), timestamp=TSC.str_to_timestamp(row['timestamp']), digest = row['digest'], filetype=FileType(row['filetype']), aanvraag_id=row['aanvraag_id']))
            return result
        else:
            return None
    def update(self, fileinfo: FileInfo):
        super().update(columns=self.__get_all_columns(False), values=self.__get_all_values(fileinfo, False), 
            where=SQE('filename', Ops.EQ, CRUD_files._filename_to_value(fileinfo.filename), no_column_ref=True))
    def delete(self, filename: str):
        super().delete(where=SQE('filename', Ops.EQ, CRUD_files._filename_to_value(filename), no_column_ref=True))

