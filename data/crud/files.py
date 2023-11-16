from data.crud.crud_base import CRUDbase
from data.crud.crud_factory import registerCRUD
from data.roots import decode_path, encode_path
from data.aapa_database import FilesTableDefinition
from data.classes.files import File
from database.database import Database
from general.timeutil import TSC

class CRUD_files(CRUDbase):
    def _after_init(self):        
        self._db_map['filename']['db2obj'] = decode_path
        self._db_map['filename']['obj2db'] = encode_path
        self._db_map['timestamp']['db2obj'] = TSC.str_to_timestamp
        self._db_map['timestamp']['obj2db'] = TSC.timestamp_to_str
        self._db_map['filetype']['db2obj'] = File.Type

registerCRUD(CRUD_files, class_type=File, table=FilesTableDefinition(),autoID=True)#, no_column_ref_for_key=True)