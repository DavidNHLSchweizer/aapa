from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.crud.crud_base import CRUDbase
from data.roots import decode_path, encode_path
from database.database import Database

class CRUD_basedirs(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, class_type=BaseDir, table=BaseDirsTableDefinition(),  autoID=True)
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path
