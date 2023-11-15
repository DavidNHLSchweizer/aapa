from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.crud.crud_base import CRUDbase
from data.crud.crud_factory import registerCRUD
from data.roots import decode_path, encode_path
from database.database import Database

class CRUD_basedirs(CRUDbase):
    def _after_init_(self):        
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path

registerCRUD(CRUD_basedirs, class_type=BaseDir, table=BaseDirsTableDefinition(),  autoID=True)