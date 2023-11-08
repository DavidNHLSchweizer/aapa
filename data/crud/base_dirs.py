from data.AAPdatabase import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.crud.crud_base import CRUDbaseAuto
from data.roots import decode_path, encode_path
from database.database import Database

class CRUD_basedirs(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, BaseDirsTableDefinition(), BaseDir)
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path
