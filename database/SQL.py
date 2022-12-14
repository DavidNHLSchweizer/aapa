from abc import ABC, abstractmethod
from database.argparser import ArgParser
from database.tabledef import ColumnDefinition, TableDefinition

class SQLFlags(ArgParser):
    COLUMNS = 1
    WHERE   = 2
    VALUES  = 3
    DISTINCT= 4
    UNIQUE  = 5
    JOINS   = 6
    flag_map = \
        [{ "flag": COLUMNS,"attribute":'arg_columns', "default":[], "key":'column'},
         { "flag": WHERE, "attribute":'where_expression', "default":None, "key":'where'},
         { "flag": VALUES, "attribute":'values', "default":[], "key":'value'},
         { "flag": DISTINCT,"attribute":'distinct', "default": False, "key":'distinct'}, 
         { "flag": UNIQUE, "attribute":'unique', "default": False, "key":'unique'},
         { "flag": JOINS, "attribute":'joins', "default":[], "key":'join'}
        ]
    def execute(self, flags, target, **args):
        self.parse_args(flags, target, self.flag_map, **args)
        
class SQLbase(ABC):
    def __init__(self, table_def: TableDefinition, **args):
        self.table_def = table_def
        SQLFlags().execute(self._getParseFlags(), self, **args)
    def __str__(self):
        return f'{self.Query}\nparams: {self.Parameters}'
    @abstractmethod
    def _getParseFlags(self):
        pass
    @abstractmethod
    def _getQuery(self):
        return ''
    @abstractmethod
    def _getParameters(self):
        return None
    @property
    def table_name(self):
        return self.table_def.table_name
    @property
    def columns(self):
        return self.table_def.columns
    @property
    def foreign_keys(self):
        return self.table_def.foreign_keys
    @property
    def Query(self):
        return self._getQuery()
    @property
    def Parameters(self):
        return self._getParameters()

class SQLcreate(SQLbase):
    def _getParseFlags(self):
        return []
    def _getQuery(self):
        def column_string(column: ColumnDefinition):
            result = f'{column.name} {column.type}'
            if column.has_primary_clause():
                result = result + ' PRIMARY KEY'
            if column.is_unique():
                result = result + ' UNIQUE'
            if column.is_notnull():
                result = result + ' NOT NULL'
            if column.has_default_value():
                result = result + f' DEFAULT {column.default_value}'
            return result
        def _nothing_to_do(self_columns):
            return len(self_columns) == 0 
        if _nothing_to_do(self.columns):
            return ''
        result = f'CREATE TABLE IF NOT EXISTS {self.table_name} ({",".join([column_string(column) for column in self.columns])}' 
        if self.table_def.is_compound_primary():
            result = result + f',PRIMARY KEY({",".join([column.name for column in self.columns if column.is_primary()])})'
        if self.table_def.has_foreign_keys():
            result  = result + ',' + ','.join([f'FOREIGN KEY({key.column_name}) REFERENCES {key.ref_table}({key.ref_column}){key.action_str()}' for key in self.table_def.foreign_keys])
#            result  = result + ',' + ','.join([str(key) for key in self.table_def.foreign_keys])
#        return f'FOREIGN KEY: {self.column_name} references {self.ref_table}.{self.ref_column}' + ondelete_str + onupdate_str

        return result + ');'
    def _getParameters(self):
        return None        
class SQLdrop(SQLbase):
    def _getParseFlags(self):
        return []
    def _getQuery(self):
        return f'DROP TABLE IF EXISTS {self.table_name};'
    def _getParameters(self):
        return None

class SQLinsert(SQLbase):
    def _getParseFlags(self):
        return [SQLFlags.COLUMNS, SQLFlags.VALUES]
    def _getQuery(self):
        def _nothing_to_do(self_columns):
            return len(self_columns) == 0 
        def _is_default_values(self_columns, insert_columns):            
            if len(insert_columns) > 0:
                return False
            else:
                return len(self_columns) == 1 and self_columns[0].primary or insert_columns == []
        if _nothing_to_do(self.columns):
            return ''
        if _is_default_values(self.columns, self.arg_columns):
            result = f'INSERT INTO {self.table_name} DEFAULT VALUES;'
        else:
            result = f'INSERT INTO {self.table_name} (' + ','.join([column for column in self.arg_columns]) + ')' + \
                      ' VALUES(' + ','.join(['?' for _ in self.arg_columns]) + ');'
        return result
    def _getParameters(self):
        return self.values
    def __init__(self, table_def, **args):
        super().__init__(table_def, **args)

class SQLcreateIndex(SQLbase):
    def __init__(self, table_def, index_name, **args):
        super().__init__(table_def, **args)
        self.index_name = index_name
    def _getParseFlags(self):
        return [SQLFlags.COLUMNS, SQLFlags.UNIQUE]
    def _getQuery(self):
        result = 'CREATE '
        if self.unique:
            result = result + 'UNIQUE '
        result = result + f'INDEX IF NOT EXISTS {self.index_name} ON {self.table_name}(' + ','.join([column for column in self.arg_columns]) + ');'
        return result
    def _getParameters(self):
        return None

class SQLselect(SQLbase):
    def _getParseFlags(self):
        return [SQLFlags.COLUMNS, SQLFlags.WHERE, SQLFlags.DISTINCT, SQLFlags.JOINS]
    def _all_columns(self):
        return not self.arg_columns or self.arg_columns == []
    def _get_table_name(self):
        result = self.table_name
        if self.joins:
            result = result + ',' + ','.join([join for join in self.joins])
        return result
    def _getQuery(self):
        result = 'SELECT '
        if self.distinct:
            result = result + 'DISTINCT '
        if self._all_columns():
            result = result + '*'
        else:
            result = result + ','.join([column for column in self.arg_columns])
        result = result + f' FROM {self._get_table_name()}'
        if self.where_expression:
            result = result + '\nWHERE ' + self.where_expression.parametrized
        return result + ';'
    def _getParameters(self):
        if not self.where_expression:
            return None
        else:
            return self.where_expression.parameters

class SQLupdate(SQLbase):
    def _getParseFlags(self):
        return [SQLFlags.COLUMNS, SQLFlags.WHERE, SQLFlags.VALUES]
    def _getQuery(self):

        # if _is_default_values(self.columns, self.arg_columns):
        #     result = f'INSERT INTO {self.table_name} DEFAULT VALUES;'
        # else:
        #     result = f'INSERT INTO {self.table_name} (' + ','.join([column for column in self.arg_columns]) + ')' + \
        #               ' VALUES(' + ','.join(['?' for _ in self.arg_columns]) + ');'

        result = f'UPDATE {self.table_name} SET ' + ','.join([f'{column}=?' for column in self.arg_columns])
        if self.where_expression:
            result = result + '\nWHERE ' + self.where_expression.parametrized
        return result + ';'
    def _getParameters(self):
        if self.where_expression:
            return [*self.values, *self.where_expression.parameters]
        else:
            return self.values

class SQLdelete(SQLbase):
    def _getParseFlags(self):
        return [SQLFlags.WHERE, SQLFlags.VALUES]
    def _getQuery(self):
        result = f'DELETE FROM {self.table_name}'
        if self.where_expression:
            result = result + '\nWHERE ' + self.where_expression.parametrized
        return result + ';'
    def _getParameters(self):
        if self.where_expression:
            return [*self.values, *self.where_expression.parameters]
        else:
            return self.values

