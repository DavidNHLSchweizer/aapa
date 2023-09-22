from data.tables.bedrijven import CRUD_bedrijven
from data.tables.studenten import CRUD_studenten
from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import AanvraagTableDefinition
from data.classes.aanvragen import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus
from database.crud import CRUDbase, StoredClass
from database.database import Database
from database.sqlexpr import Ops
from general.keys import get_next_key

class CRUD_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition(), AanvraagInfo)
        self._db_map['stud_nr']['attrib'] = 'student.stud_nr'
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
    def create(self, aanvraag: AanvraagInfo):        
        aanvraag.id = get_next_key(AanvraagTableDefinition.KEY_FOR_ID) #TODO: mogelijk kan dit anders, maar nodig is het niet erg
        super().create(aanvraag)
    def _read_sub_attrib(self, sub_attrib_name: str, value)->StoredClass:
        match sub_attrib_name:
            case 'stud_nr': return CRUD_studenten(self.database).read(value)
            case 'id': return CRUD_bedrijven(self.database).read(value)
            case _: return None
    # def update(self, aanvraag: AanvraagInfo):
    #     super().update(columns=self._get_all_columns(False), 
    #                 values=self._get_all_values(aanvraag, False), where=SQE('id', Ops.EQ, aanvraag.id))
        


