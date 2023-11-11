from data.classes.bedrijven import Bedrijf
from data.crud.bedrijven import CRUD_bedrijven
from data.AAPdatabase import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.crud_base import CRUDbaseAuto
from data.crud.milestones import CRUD_milestones
from data.crud.studenten import CRUD_studenten
from database.database import Database

class CRUD_aanvragen(CRUD_milestones):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition(), Aanvraag, master_CRUD=CRUD_milestones(database))
        self._db_map['status']['db2obj'] = Aanvraag.Status
        self._db_map['beoordeling']['db2obj'] = Aanvraag.Beoordeling
