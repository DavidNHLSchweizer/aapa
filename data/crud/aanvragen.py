from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.crud.milestones import CRUD_milestones
from data.AAPdatabase import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.crud_base import CRUDbaseAuto
from database.database import Database

class CRUD_aanvragen(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition(), Aanvraag)
        self.crud_base_table = CRUD_milestones(database)
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
        self._db_map['status']['db2obj'] = Aanvraag.Status
        self._db_map['beoordeling']['db2obj'] = Aanvraag.Beoordeling
    def _read_sub_attrib(self, sub_attrib_name: str, value)->Bedrijf:
        match sub_attrib_name:
            case 'id': return CRUD_bedrijven(self.database).read(value)
            case _: return None
    def create(self, aanvraag: Aanvraag):
        self.crud_base_table.create(aanvraag)
        super().create(aanvraag)
        self.database.create_record(self.table, columns=self._get_all_columns(), values=self._get_all_values(aapa_obj)) 


