from data.roots import decode_path, encode_path
from data.AAPdatabase import FileTableDefinition
from data.classes.files import File
from data.crud.crud_base import CRUDbase
from database.database import Database
from general.timeutil import TSC

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FileTableDefinition(), File, no_column_ref_for_key=True)
        self._db_map['filename']['db2obj'] = decode_path
        self._db_map['filename']['obj2db'] = encode_path
        self._db_map['timestamp']['db2obj'] = TSC.str_to_timestamp
        self._db_map['timestamp']['obj2db'] = TSC.timestamp_to_str
    def read_all(self, filenames: list[str])->list[File]:
        return [self.read(filename) for filename in filenames]

