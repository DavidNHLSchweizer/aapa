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
    def __get_all_columns(self, include_key = True):
        result = ['id'] if include_key else []
        result.extend(['stud_nr', 'bedrijf_id', 'datum_str', 'titel', 'aanvraag_nr', 'beoordeling', 'status'])
        return result
    @staticmethod
    def __beoordeling_to_value(beoordeling: AanvraagBeoordeling):
        return beoordeling.value
    @staticmethod
    def __status_to_value(status: AanvraagStatus):
        return status.value
    def __get_all_values(self, docInfo: AanvraagInfo, include_key = True):
        result = [docInfo.id] if include_key else []
        result.extend([docInfo.student.studnr, docInfo.bedrijf.id, docInfo.datum_str, docInfo.titel, docInfo.aanvraag_nr, CRUD_aanvragen.__beoordeling_to_value(docInfo.beoordeling), CRUD_aanvragen.__status_to_value(docInfo.status)])
        return result
    def create(self, docInfo: AanvraagInfo):        
        docInfo.id = get_next_key(AanvraagTableDefinition.KEY_FOR_ID)
        super().create(columns=self.__get_all_columns(False), values=self.__get_all_values(docInfo, False))
    def __build_aanvraag(self, row)->AanvraagInfo:
        student = CRUD_studenten(self.database).read(row['stud_nr'])
        bedrijf = CRUD_bedrijven(self.database).read(row['bedrijf_id'])
        result =  AanvraagInfo(student, bedrijf=bedrijf, datum_str=row['datum_str'], titel=row['titel'],beoordeling=AanvraagBeoordeling(row['beoordeling']), status=AanvraagStatus(row['status']), id=row['id'], aanvraag_nr=row['aanvraag_nr'])
        return result
    def read(self, id: int)->AanvraagInfo:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return self.__build_aanvraag(row)
        else:
            return None
    def update(self, docInfo: AanvraagInfo):
        super().update(columns=self.__get_all_columns(False), 
                    values=self.__get_all_values(docInfo, False), where=SQE('id', Ops.EQ, docInfo.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))

