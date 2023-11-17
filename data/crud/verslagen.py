from typing import Any
from data.crud.crud_const import AAPAClass, DBtype
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.crud.adapters import ColumnAdapter, FilenameColumnAdapter
from data.crud.crud_base import CRUD
from data.crud.crud_factory import registerCRUD
from data.crud.milestones import CRUD_milestones
from data.roots import decode_path, encode_path
from database.database import Database
from database.table_def import TableDefinition


class VerslagStatusColumnAdapter(ColumnAdapter):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Status(db_value)
class VerslagBeoordelingColumnAdapter(ColumnAdapter):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Beoordeling(db_value)

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
                self.adapter.set_adapter(FilenameColumnAdapter('directory'))
                self.adapter.set_adapter(VerslagStatusColumnAdapter('status'))
                self.adapter.set_adapter(VerslagBeoordelingColumnAdapter('beoordeling'))
        return verslag

registerCRUD(CRUD_verslagen, class_type=Verslag, table=VerslagTableDefinition(), autoID=True)