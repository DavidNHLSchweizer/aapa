from typing import Iterable
from data.roots import decode_path, encode_path
from data.AAPdatabase import FilesTableDefinition
from data.classes.files import File
from data.crud.crud_base import CRUDbaseAuto
from database.database import Database
from general.timeutil import TSC

class CRUD_files(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, FilesTableDefinition(), File)#, no_column_ref_for_key=True)
        self._db_map['filename']['db2obj'] = decode_path
        self._db_map['filename']['obj2db'] = encode_path
        self._db_map['timestamp']['db2obj'] = TSC.str_to_timestamp
        self._db_map['timestamp']['obj2db'] = TSC.timestamp_to_str
        self._db_map['filetype']['db2obj'] = File.Type
    
