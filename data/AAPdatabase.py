from pickle import EMPTY_DICT
from data.aanvraag_info import AanvraagDocumentInfo, Bedrijf
from database.SQL import SQLbase, SQLdelete, SQLcreate, SQLselect, SQLupdate
from database.crud import CRUDbase
from database.sqlexpr import Ops, SQLexpression as SQE
from database.tabledef import ForeignKeyAction, TableDefinition
from database.database import Database, Schema
# from data.units import Module, Pakket, Toets, Toetseenheid
import database.dbConst as dbc

class StudentTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENTEN')
        self.add_column('stud_nr', dbc.TEXT, primary=True)
        self.add_column('full_name', dbc.TEXT)
        self.add_column('first_name', dbc.TEXT)
        self.add_column('email', dbc.TEXT)
        self.add_column('tel_nr', dbc.TEXT)

class BedrijfTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BEDRIJVEN', autoid=True)
        self.add_column('name', dbc.TEXT)

class AanvraagTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN', autoid = True)
        self.add_column('filename', dbc.TEXT)
        self.add_column('stud_nr', dbc.TEXT)
        self.add_column('bedrijf_id', dbc.INTEGER)
        self.add_column('datum_str', dbc.TEXT)
        self.add_column('titel', dbc.TEXT)
        self.add_column('beoordeling', dbc.INTEGER)

class FileTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILES')
        self.add_column('filename', dbc.TEXT, primary=True)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)

class AAPSchema(Schema):
    def __init__(self):
        super().__init__()
        self.add_table(StudentTableDefinition())
        self.add_table(BedrijfTableDefinition())
        self.add_table(AanvraagTableDefinition())
        self.add_table(FileTableDefinition())
        self.__define_foreign_keys()
    def __define_foreign_keys(self):
        self.table('AANVRAGEN').add_foreign_key('stud_nr', 'STUDENTEN', 'stud_nr', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.table('AANVRAGEN').add_foreign_key('bedrijf_id', 'BEDRIJVEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.table('AANVRAGEN').add_foreign_key('filename', 'FILES', 'filename', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class AAPDatabase(Database):
    def __init__(self, filename):
        super().__init__(filename)
        self.schema = Schema()
        self.schema.read_from_database(self)


    # def write_pakket(self, pakket: Pakket):
    #     self.execute_sql_command(SQLinsert(self.schema.table('PAKKETTEN'), columns=['pakket_naam'], values=[pakket.naam]))
    #     self.commit()
    #     for module in pakket.modules:
    #         self._write_module(module, pakket.naam)
    # def read_pakket(self, pakket_naam: str)->Pakket:
    #     self.log_info(f'read_pakket: {pakket_naam}')
    #     if self.execute_select(SQLselect(self.schema.table('PAKKETTEN'), where=SQE('pakket_naam', Ops.EQ, pakket_naam))):
    #         PB = PakketBuilder(pakket_naam)
    #         self._read_modules(PB, pakket_naam)
    #         return PB.pakket
    #     return None
    # def _write_module(self, module: Module, pakket_naam: str):
    #     self.execute_sql_command(SQLinsert(self.schema.table('MODULES'), columns=['code', 'naam'], values=[module.code, module.naam]))
    #     self.execute_sql_command(SQLinsert(self.schema.table('PAKKET_MODULES'), columns=['pakket_naam', 'module_code'], values=[pakket_naam, module.code]))
    #     self.commit()
    #     for toetseenheid in module.toetseenheden:
    #         self._write_toetseenheid(toetseenheid, module.code)
    # def _write_toetseenheid(self, toetseenheid: Toetseenheid, module_code: str):
    #     self.execute_sql_command(SQLinsert(self.schema.table('TOETSEENHEDEN'), columns=['code', 'naam', 'te_behalen'], values=[toetseenheid.code, toetseenheid.naam, toetseenheid.te_behalen]))
    #     self.execute_sql_command(SQLinsert(self.schema.table('MODULE_TOETSEENHEDEN'), columns=['module_code', 'toetseenheid_code'], values=[module_code, toetseenheid.code]))
    #     self.commit()
    #     for toets in toetseenheid.toetsen:
    #         self._write_toets(toets, toetseenheid.code)
    # def _write_toets(self, toets: Toets, toetseenheid_code: str):
    #     self.execute_sql_command(SQLinsert(self.schema.table('TOETSEN'), columns=['code', 'naam', 'cesuur'], values=[toets.code, toets.naam, toets.cesuur]))
    #     self.execute_sql_command(SQLinsert(self.schema.table('TOETSEENHEID_TOETSEN'), columns=['toetseenheid_code', 'toets_code'], values=[toetseenheid_code, toets.code]))
    #     self.commit()
    # def read_pakket(self, pakket_naam: str)->Pakket:
    #     self.log_info(f'read_pakket: {pakket_naam}')
    #     if self.execute_select(SQLselect(self.schema.table('PAKKETTEN'), where=SQE('pakket_naam', Ops.EQ, pakket_naam))):
    #         PB = PakketBuilder(pakket_naam)
    #         self._read_modules(PB, pakket_naam)
    #         return PB.pakket
    #     return None
    # def _read_modules(self, PB: PakketBuilder, pakket_naam: str):
    #     join_clause = SQE('PAKKET_MODULES.module_code', Ops.EQ, 'MODULES.code')
    #     where_clause = SQE('pakket_naam', Ops.EQ, pakket_naam)
    #     for module in self.execute_select(SQLselect(self.schema.table('PAKKET_MODULES'), join='MODULES',columns=['MODULES.code', 'MODULES.naam'], where=SQE(join_clause, Ops.AND, where_clause))):
    #         PB.add_module(module['code'], module['naam'])
    #         self._read_toetseenheden(PB, module['code'])
    # def _read_toetseenheden(self, PB: PakketBuilder, module_code: str):
    #     join_clause = SQE('TOETSEENHEDEN.code', Ops.EQ, 'MODULE_TOETSEENHEDEN.toetseenheid_code')
    #     where_clause = SQE('module_code', Ops.EQ, module_code)
    #     for toetseenheid in self.execute_select(SQLselect(self.schema.table('MODULE_TOETSEENHEDEN'), join='TOETSEENHEDEN', columns=['TOETSEENHEDEN.code', 'TOETSEENHEDEN.naam', 'TOETSEENHEDEN.te_behalen'], where=SQE(join_clause, Ops.AND, where_clause))):
    #         PB.add_toetseenheid(toetseenheid['code'], toetseenheid['naam'], toetseenheid['te_behalen'])
    #         self._read_toetsen(PB, toetseenheid['code'])
    # def _read_toetsen(self, PB: PakketBuilder, toetseenheid_code: str):
    #     join_clause = SQE('TOETSEN.code', Ops.EQ, 'TOETSEENHEID_TOETSEN.toets_code')
    #     where_clause = SQE('toetseenheid_code', Ops.EQ, toetseenheid_code)
    #     for toets in self.execute_select(SQLselect(self.schema.table('TOETSEENHEID_TOETSEN'), join='TOETSEN', columns=['TOETSEN.code', 'TOETSEN.naam', 'TOETSEN.cesuur'], where=SQE(join_clause, Ops.AND, where_clause))):
    #         PB.add_toets(toets['code'], toets['naam'], toets['cesuur'])
    # def delete_pakket(self, pakket: Pakket):
    #     for module in pakket.modules:
    #         self._delete_module(module) 
    #     self.execute_sql_command(SQLdelete(self.schema.table('PAKKETTEN'), where=SQE('pakket_naam', Ops.EQ, pakket.naam)))
    #     self.commit()
    # def _delete_module(self, module: Module):
    #     for toetseenheid in module.toetseenheden:
    #         self._delete_toetseenheid(toetseenheid)
    #     self.execute_sql_command(SQLdelete(self.schema.table('MODULES'), where=SQE('code', Ops.EQ, module.code)))
    # def _delete_toetseenheid(self, toetseenheid: Toetseenheid):
    #     self.execute_sql_command(SQLdelete(self.schema.table('TOETSEN'), where=SQE('code', Ops.IN, [toets.code for toets in toetseenheid.toetsen])))
    #     self.execute_sql_command(SQLdelete(self.schema.table('TOETSEENHEDEN'), where=SQE('code', Ops.EQ, toetseenheid.code)))
        
