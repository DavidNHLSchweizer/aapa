from data.classes.bedrijven import Bedrijf
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition, VerslagenViewDefinition
from data.crud.crud_base import CRUDbase
from data.crud.milestones import CRUD_milestones
from data.crud.studenten import CRUD_studenten
from data.roots import decode_path, encode_path
from database.database import Database
from general.timeutil import TSC

class CRUD_verslagen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, class_type=Verslag, table=VerslagTableDefinition(), 
                         view=VerslagenViewDefinition(), details=[CRUD_milestones(database)], autoID=True)
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path
    def _post_process_read(self, aapa_obj: Verslag)->Verslag:
        #corrects status and beoordeling types (read as ints from database) 
        aapa_obj.status = Verslag.Status(aapa_obj.status)
        aapa_obj.beoordeling = Verslag.Beoordeling(aapa_obj.beoordeling)
        return aapa_obj 

