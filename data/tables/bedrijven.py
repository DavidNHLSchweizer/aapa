from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from database.crud import CRUDbase, DBtype
from database.database import Database
from database.sqlexpr import Ops
from general.keys import get_next_key

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition(), Bedrijf)
    def create(self, bedrijf: Bedrijf):
        bedrijf.id = get_next_key(BedrijfTableDefinition.KEY_FOR_ID)
        super().create(bedrijf)   
    # def update(self, bedrijf: Bedrijf):
    #     super().update(columns=self._get_all_columns(False), values=self._get_all_values(bedrijf, False), where=SQE('id', Ops.EQ, bedrijf.id))
