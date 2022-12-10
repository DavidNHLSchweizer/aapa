
from abc import ABC, abstractmethod
from database.tabledef import TableDefinition


class CRUD(ABC):
    def __init__(self, tabledef: TableDefinition, object_class):
        self.tabledef = tabledef
        self.object_class = object_class
        
    @abstractmethod
    def create_object(self, **kwargs)->object: pass
    def read_object(self, **kwargs):pass

class StudentCRUD(CRUD)
    def write_pakket(self, pakket: Pakket):
        self.execute_sql_command(SQLinsert(self.schema.table('PAKKETTEN'), columns=['pakket_naam'], values=[pakket.naam]))
        self.commit()
        for module in pakket.modules:
            self._write_module(module, pakket.naam)
    def read_pakket(self, pakket_naam: str)->Pakket:
        self.log_info(f'read_pakket: {pakket_naam}')
        if self.execute_select(SQLselect(self.schema.table('PAKKETTEN'), where=SQE('pakket_naam', Ops.EQ, pakket_naam))):
            PB = PakketBuilder(pakket_naam)
            self._read_modules(PB, pakket_naam)
            return PB.pakket
        return None
    # def _write_toetseenheid(self, toetseenheid: Toetseenheid, module_code: str):
    #     self.execute_sql_command(SQLinsert(self.schema.table('TOETSEENHEDEN'), columns=['code', 'naam', 'te_behalen'], values=[toetseenheid.code, toetseenheid.naam, toetseenheid.te_behalen]))
    #     self.execute_sql_command(SQLinsert(self.schema.table('MODULE_TOETSEENHEDEN'), columns=['module_code', 'toetseenheid_code'], values=[module_code, toetseenheid.code]))
    #     self.commit()
    #     for toets in toetseenheid.toetsen:
    #         self._write_toets(toets, toetseenheid.code)
    #     join_clause = SQE('TOETSEENHEDEN.code', Ops.EQ, 'MODULE_TOETSEENHEDEN.toetseenheid_code')
    #     where_clause = SQE('module_code', Ops.EQ, module_code)
    #     for toetseenheid in self.execute_select(SQLselect(self.schema.table('MODULE_TOETSEENHEDEN'), join='TOETSEENHEDEN', columns=['TOETSEENHEDEN.code', 'TOETSEENHEDEN.naam', 'TOETSEENHEDEN.te_behalen'], where=SQE(join_clause, Ops.AND, where_clause))):
    #         PB.add_toetseenheid(toetseenheid['code'], toetseenheid['naam'], toetseenheid['te_behalen'])
    #         self._read_toetsen(PB, toetseenheid['code'])
