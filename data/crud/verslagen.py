from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.crud.crud_base import AAPAClass, CRUDbase
from data.crud.crud_factory import registerCRUD
from data.crud.milestones import CRUD_milestones
from data.roots import decode_path, encode_path
from database.database import Database
from database.table_def import TableDefinition

class CRUD_verslagen(CRUD_milestones):
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                    # superclass_CRUDs: list[CRUDbase] = [], 
                    subclass_CRUDs:dict[str, AAPAClass]={}, 
                    no_column_ref_for_key = False, autoID=False):
        super().__init__(database, class_type=class_type, table=table, 
                        #  superclass_CRUDs=superclass_CRUDs, 
                        subclass_CRUDs=subclass_CRUDs,
                         no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)        
    def _after_init(self):        
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path
    def _post_process_read(self, aapa_obj: Verslag)->Verslag:
        #corrects status and beoordeling types (read as ints from database) 
        aapa_obj.status = Verslag.Status(aapa_obj.status)
        aapa_obj.beoordeling = Verslag.Beoordeling(aapa_obj.beoordeling)
        return aapa_obj 

registerCRUD(CRUD_verslagen, class_type=Verslag, table=VerslagTableDefinition(), 
                        #  details=[CRUD_milestones(database)], 
                         autoID=True)