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
        self._db_map['filename']['db2obj'] = encode_path
        self._db_map['timestamp']['db2obj'] = TSC.timestamp_to_str
    # def create(self, fileinfo: FileInfo):
    #     super().create(columns=self._get_all_columns(), values=self._get_all_values(fileinfo))   
    def read(self, filename: str)->FileInfo:
        if row:=super().read(where=SQE('filename', Ops.EQ, self.map_object_to_db('filename', filename), no_column_ref = True)):
            return FileInfo(decode_path(filename), timestamp=TSC.str_to_timestamp(row['timestamp']), digest = row['digest'], filetype=FileType(row['filetype']), aanvraag_id=row['aanvraag_id'])
        else:
            return None
    def read_all(self, filenames: list[str])->list[FileInfo]:
        if rows:=super().read(where=SQE(self.table.keys[0], Ops.IN, [self.map_object_to_db('filename', filename) for filename in filenames], 
                                        no_column_ref = True), multiple=True):
            result = []
            for row in rows:
                result.append(FileInfo(decode_path(row['filename']), timestamp=TSC.str_to_timestamp(row['timestamp']), digest = row['digest'], filetype=FileType(row['filetype']), aanvraag_id=row['aanvraag_id']))
            return result
        else:
            return None
    def update(self, fileinfo: FileInfo):
        super().update(columns=self._get_all_columns(False), values=self._get_all_values(fileinfo, False), 
            where=SQE(self.table.keys[0], Ops.EQ, self.map_object_to_db('filename', fileinfo.filename), no_column_ref=True))
    # def delete(self, filename: str):
    #     super().delete(where=SQE(self.table.keys[0], Ops.EQ, self.map_object_to_db('filename', filename), no_column_ref=True))

