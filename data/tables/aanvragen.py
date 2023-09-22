from data.tables.bedrijven import CRUD_bedrijven
from data.tables.studenten import CRUD_studenten
from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import AanvraagTableDefinition
from data.classes import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops
from general.keys import get_next_key

class CRUD_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition())
        self._db_map['stud_nr']['attrib'] = 'student.studnr'
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
    def create(self, aanvraag: AanvraagInfo):        
        aanvraag.id = get_next_key(AanvraagTableDefinition.KEY_FOR_ID)
        super().create(aanvraag)
    def __build_aanvraag(self, row)->AanvraagInfo:
        student = CRUD_studenten(self.database).read(row['stud_nr'])
        bedrijf = CRUD_bedrijven(self.database).read(row['bedrijf_id'])
        result =  AanvraagInfo(student, bedrijf=bedrijf, datum_str=row['datum_str'], titel=row['titel'],beoordeling=AanvraagBeoordeling(row['beoordeling']), status=AanvraagStatus(row['status']), id=row['id'], aanvraag_nr=row['aanvraag_nr'])
        return result
    def read(self, id: int)->AanvraagInfo:
        if row:=super().read(id):
            return self.__build_aanvraag(row)
        else:
            return None
    def update(self, docInfo: AanvraagInfo):
        super().update(columns=self._get_all_columns(False), 
                    values=self._get_all_values(docInfo, False), where=SQE('id', Ops.EQ, docInfo.id))
        


