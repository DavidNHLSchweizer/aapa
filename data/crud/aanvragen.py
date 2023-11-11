from data.classes.bedrijven import Bedrijf
from data.crud.bedrijven import CRUD_bedrijven
from data.AAPdatabase import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.crud_base import CRUDbaseAuto
from data.crud.studenten import CRUD_studenten
from database.database import Database

class CRUD_aanvragen(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition(), Aanvraag)
        # self._db_map['stud_id']['attrib'] = 'student.id'
        # self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
        # self._db_map['status']['db2obj'] = Aanvraag.Status
        # self._db_map['beoordeling']['db2obj'] = Aanvraag.Beoordeling
    def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->Bedrijf:
        if sub_attrib_name == 'id':
            match main_part:
                case 'student': 
                    return CRUD_studenten(self.database).read(value)
                case 'bedrijf': 
                    return CRUD_bedrijven(self.database).read(value)
        return None

