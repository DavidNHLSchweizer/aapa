from pickle import EMPTY_DICT
from data.aanvraag_info import AanvraagInfo, Bedrijf
from database.SQL import SQLbase, SQLdelete, SQLcreate, SQLselect, SQLupdate
from database.crud import CRUDbase
from database.sqlexpr import Ops, SQLexpression as SQE
from database.tabledef import ForeignKeyAction, TableDefinition
from database.database import Database, Schema
# from data.units import Module, Pakket, Toets, Toetseenheid
import database.dbConst as dbc
from general.keys import reset_key

class StudentTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENTEN')
        self.add_column('stud_nr', dbc.TEXT, primary=True)
        self.add_column('full_name', dbc.TEXT)
        self.add_column('first_name', dbc.TEXT)
        self.add_column('email', dbc.TEXT)
        self.add_column('tel_nr', dbc.TEXT)
        self.add_column('aanvragen', dbc.INTEGER)

class BedrijfTableDefinition(TableDefinition):
    KEY_FOR_ID = 'Bedrijf' # key in general.keys used to generate IDs
    def __init__(self):
        super().__init__('BEDRIJVEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('name', dbc.TEXT)    

class AanvraagTableDefinition(TableDefinition):
    KEY_FOR_ID  = 'Aanvraag' 
    def __init__(self):
        super().__init__('AANVRAGEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_nr', dbc.TEXT)
        self.add_column('bedrijf_id', dbc.INTEGER)
        self.add_column('datum_str', dbc.TEXT)
        self.add_column('titel', dbc.TEXT)
        self.add_column('versie', dbc.INTEGER)
        self.add_column('status', dbc.INTEGER)
        self.add_column('beoordeling', dbc.INTEGER)

class FileTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILES')
        self.add_column('filename', dbc.TEXT, primary=True)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)
        self.add_column('aanvraag_id', dbc.INTEGER)

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
        # self.table('AANVRAGEN').add_foreign_key('filename', 'FILES', 'filename', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.table('FILES').add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class AAPDatabase(Database):
    def __init__(self, filename, _reset_flag = False):
        super().__init__(filename, _reset_flag)
        self.schema = Schema()
        self.schema.read_from_database(self)        
        if not self._reset_flag:
            self.reset_keys()
    def reset_keys(self):
        reset_key(BedrijfTableDefinition.KEY_FOR_ID, self.__find_max_key('BEDRIJVEN'))
        reset_key(AanvraagTableDefinition.KEY_FOR_ID, self.__find_max_key('AANVRAGEN'))
    def __find_max_key(self, table_name: str):
        if (row := self._execute_sql_command(f'select max(ID) from {table_name};', return_values = True)) and \
                                            (r0 := list(row[0])[0]):
            return r0 
        else:
            return 0
        
