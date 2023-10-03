from enum import Enum
import database.dbConst as dbc
from database.dbargparser import dbArgParser

class ColumnFlags(dbArgParser):
    PRIMARY = 1
    NOTNULL = 2
    UNIQUE  = 3
    DEFAULT = 4
    ALL     = [PRIMARY, NOTNULL, UNIQUE, DEFAULT]
    flag_map = \
        [{ "flag": PRIMARY, "attribute":'primary', "default":False, "key":'primary'},
         { "flag": NOTNULL, "attribute":'notnull', "default":False, "key":'notnull'},
         { "flag": UNIQUE, "attribute":'unique', "default": False, "key":'unique'},
         { "flag": DEFAULT, "attribute":'default_value', "default": None, "key":'default_value'},
        ]
    @staticmethod
    def get_attributes_for_flag(flags):
        result = []
        for flag in ColumnFlags.flag_map:
            if flag["flag"] in flags:
                result.append({"attribute": flag["attribute"], "default":flag["default"]})    
        return result
    @staticmethod
    def get_attributes_for_args(**args):
        class empty_target:
            pass
        result = []        
        e = empty_target()
        ColumnFlags().execute(empty_target, **args)
        for flag in ColumnFlags.flag_map:
            if hasattr(empty_target, flag["attribute"]) and getattr(empty_target, flag["attribute"]) != flag["default"]:
                result.append({"attribute": flag["attribute"], "default":flag["default"]})    
        return result
    def execute(self, target, **args):
        self.parse(ColumnFlags.ALL, target, ColumnFlags.flag_map, **args)
  
class ColumnDefinition:
    def __init__(self, name, type, **args):
        self.name = name
        self.type = type
        self._compound_primary = False # SQLite doesn't support multiple PRIMARY KEY columns
        #TODO: wat hier boven staat lijkt helemaal niet te kloppen, consequentie is niet helemaal duidelijk
        ColumnFlags().execute(self, **args)
    def is_primary(self):
        return hasattr(self, 'primary') and self.primary 
    def has_primary_clause(self):
        return self.is_primary() and not self._compound_primary
    def is_notnull(self):
        return hasattr(self, 'notnull') and self.notnull
    def is_unique(self):
        return hasattr(self, 'unique') and self.unique
    def has_default_value(self):
        return hasattr(self, 'default_value') and self.default_value
    def __str__(self):
        result = f'{self.name} {self.type}'
        if self.has_primary_clause():
            result = result + ' PRIMARY'
        if self.is_notnull():
            result = result + ' NOT NULL'
        if self.is_unique():
            result = result + ' UNIQUE'
        if self.has_default_value():
            result = result + f' DEFAULT ({self.default_value})'
        return result

class ForeignKeyAction(Enum):
    NOACTION    = 'NO ACTION'
    RESTRICT    = 'RESTRICT'
    SETNULL     = 'SET NULL'
    SETDEFAULT  = 'SET DEFAULT'
    CASCADE     = 'CASCADE'
    def __str__(self):
        return self.value

class ForeignKeyDefinition:
    def __init__(self, column_name, ref_table, ref_column, onupdate: ForeignKeyAction = None, ondelete: ForeignKeyAction = None):
        self.column_name = column_name
        self.ref_table = ref_table
        self.ref_column = ref_column
        self.onupdate = onupdate
        self.ondelete = ondelete
    def action_str(self):
        def on_str(on_type, value):
            if value == ForeignKeyAction.NOACTION.value:
                return ''
            else:
                return f' ON {on_type} {value}' if value else '' 
        return on_str('UPDATE', self.onupdate) + on_str('DELETE', self.ondelete)
    def __str__(self):
        return f'FOREIGN KEY {self.column_name} references {self.ref_table}.{self.ref_column}' + self.action_str()

class TableFlags(dbArgParser):
    AUTOID  = 1
    ALL     = [AUTOID]
    flag_map = \
        [
         { "flag": AUTOID,"attribute":'autoID', "default":False, "key":'autoid'}
        ]
    def execute(self, target, **args):
        self.parse(TableFlags.ALL, target, TableFlags.flag_map, **args)

class TableDefinition:
    def __init__(self, name, **args):
        self.name = name
        self.columns:list[ColumnDefinition] = []
        self.foreign_keys = []
        self.keys:list[str] = []
        self.__has_primary = False
        self.__has_compound_primary = False
        TableFlags().execute(self, **args)
        if self.autoID:
            self.add_column(dbc.ID, dbc.INTEGER, primary=True)
    @property 
    def key(self)->str:
        return self.keys[0] if len(self.keys) > 0 else None 
    def add_column(self, column_name, column_type, **args):
        self.columns.append(column:=ColumnDefinition(column_name, column_type, **args))
        if column.is_primary():
            self.keys.append(column.name)
            if self.__has_compound_primary:
                column._compound_primary = True
            elif self.__has_primary:
                self.__has_compound_primary = True
                for c in self.columns:
                    if c.is_primary():
                        c._compound_primary = True
            else:
                self.__has_primary = True
    def add_foreign_key(self, column_name, ref_table, ref_column, onupdate=None, ondelete=None):
        self.foreign_keys.append(ForeignKeyDefinition(column_name, ref_table, ref_column, onupdate, ondelete))
    def is_compound_primary(self):
        return self.__has_compound_primary
    def has_foreign_keys(self):
        return len(self.foreign_keys) > 0
    def __str__(self):
        result = f'TABLE {self.name}'
        if len(self.columns):
            result = result + '\nCOLUMNS:\n\t' + '\n\t'.join([str(column) for column in self.columns])
        if self.is_compound_primary():
            result = result + '\n\tPRIMARY KEY(' + ','.join([column.name for column in self.columns if column.is_primary()]) + ')'
        if self.has_foreign_keys():
            result = result + '\n\t' + '\n\t'.join([str(key) for key in self.foreign_keys])
        return result

