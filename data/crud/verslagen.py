from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.crud.crud_base import CRUD, AAPAClass, CRUDbase
from data.crud.crud_factory import registerCRUD
from data.crud.milestones import CRUD_milestones
from data.roots import decode_path, encode_path
from database.database import Database
from database.table_def import TableDefinition

class CRUD_verslagen(CRUD_milestones):
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                    subclass_CRUDs:dict[str, AAPAClass]={}, 
                    no_column_ref_for_key = False, autoID=False):
        super().__init__(database, class_type=class_type, table=table, 
                        subclass_CRUDs=subclass_CRUDs,
                         no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)        
    def _post_action(self, verslag: Verslag, crud_action: CRUD)->Verslag:        
        match crud_action:
            case CRUD.INIT:
                super()._post_action(verslag, crud_action)
                self._db_map['directory']['db2obj'] = decode_path
                self._db_map['directory']['obj2db'] = encode_path
                self._db_map['status']['db2obj'] = Verslag.Status
                self._db_map['beoordeling']['db2obj'] = Verslag.Beoordeling
        return verslag

registerCRUD(CRUD_verslagen, class_type=Verslag, table=VerslagTableDefinition(), autoID=True)