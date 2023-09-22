from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import BedrijfTableDefinition
from data.classes import Bedrijf
from database.crud import CRUDbase, DBtype
from database.database import Database
from database.sqlexpr import Ops
from general.keys import get_next_key

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition())
        self._db_map['name']['attrib'] = 'bedrijfsnaam'
    def create(self, bedrijf: Bedrijf):
        bedrijf.id = get_next_key(BedrijfTableDefinition.KEY_FOR_ID)
        super().create(bedrijf)   
    # def read(self, id: int)->Bedrijf:
    #     if row:=super().read(id):
    #         return Bedrijf(row['name'], id)
    #     else:
    #         return None
    def update(self, bedrijf: Bedrijf):
        super().update(columns=self._get_all_columns(False), values=self._get_all_values(bedrijf, False), where=SQE('id', Ops.EQ, bedrijf.id))
    # def delete(self, id: int):
    #     super().delete(where=SQE(self.table.keys[0], Ops.EQ, id))
