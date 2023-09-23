from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.crud.studenten import CRUD_studenten
from data.AAPdatabase import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.crud_base import CRUDbase
from database.database import Database
from general.keys import get_next_key

class CRUD_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition(), Aanvraag)
        self._db_map['stud_nr']['attrib'] = 'student.stud_nr'
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
    def create(self, aanvraag: Aanvraag):        
        aanvraag.id = get_next_key(AanvraagTableDefinition.KEY_FOR_ID) #TODO: mogelijk kan dit anders, maar nodig is het niet erg
        super().create(aanvraag)
    def _read_sub_attrib(self, sub_attrib_name: str, value)->type[Student|Bedrijf]:
        match sub_attrib_name:
            case 'stud_nr': return CRUD_studenten(self.database).read(value)
            case 'id': return CRUD_bedrijven(self.database).read(value)
            case _: return None


