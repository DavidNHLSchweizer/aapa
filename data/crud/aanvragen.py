from data.classes.bedrijven import Bedrijf
from data.crud.bedrijven import CRUD_bedrijven
from data.aapa_database import AanvraagTableDefinition, AanvragenViewDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.milestones import CRUD_milestones
from data.crud.crud_base import CRUDbase
from data.crud.studenten import CRUD_studenten
from database.database import Database

class CRUD_aanvragen(CRUDbase):
    def __init__(self, database: Database):        
        super().__init__(database, class_type=Aanvraag, table=AanvraagTableDefinition(), 
                         view=AanvragenViewDefinition(), details=[CRUD_milestones(database)], autoID=True)
        self._db_map['status']['db2obj'] = Aanvraag.Status
        self._db_map['beoordeling']['db2obj'] = Aanvraag.Beoordeling
