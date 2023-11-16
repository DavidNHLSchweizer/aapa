from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.crud.crud_base import CRUD, CRUDbase
from data.crud.crud_factory import registerCRUD
from data.roots import decode_path, encode_path

class CRUD_basedirs(CRUDbase):
    def _post_action(self, basedir: BaseDir, crud_action: CRUD)->BaseDir:        
        match crud_action:
            case CRUD.INIT:
                self._db_map['directory']['db2obj'] = decode_path
                self._db_map['directory']['obj2db'] = encode_path
            case _: pass
        return basedir

registerCRUD(CRUD_basedirs, class_type=BaseDir, table=BaseDirsTableDefinition(),  autoID=True)