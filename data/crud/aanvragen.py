from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.crud.studenten import CRUD_studenten
from data.AAPdatabase import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.crud_base import CRUDbaseAuto
from database.database import Database

class CRUD_aanvragen(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition(), Aanvraag)
        self._db_map['stud_nr']['attrib'] = 'student.stud_nr'
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
        self._db_map['status']['db2obj'] = Aanvraag.Status
        self._db_map['beoordeling']['db2obj'] = Aanvraag.Beoordeling
    def _read_sub_attrib(self, sub_attrib_name: str, value)->type[Student|Bedrijf]:
        match sub_attrib_name:
            case 'stud_nr': return CRUD_studenten(self.database).read(value)
            case 'id': return CRUD_bedrijven(self.database).read(value)
            case _: return None


