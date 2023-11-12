from dataclasses import dataclass
from database.sql_base import SQLFlags, SQLbase, SQLselectBase
from database.table_def import ColumnDefinition, ForeignKeyDefinition, IndexDefinition, TableDefinition

klote alias werkt nog niet.
@dataclass
class TableData:
    table_def: TableDefinition = None
    alias: str = ''
    @property
    def table_name(self)->str:
        if self.alias:
            return f'{self.table_def.name} as {self.alias}'
        else:
            return self.table_def.name
    @property
    def columns(self)->list[ColumnDefinition]:
        return self.table_def.columns
    @property
    def foreign_keys(self)->list[ForeignKeyDefinition]:
        return self.table_def.foreign_keys

class SQLTablebase(SQLbase):
    def __init__(self, table_def: TableDefinition, **args):
        super().__init__(**args)
        self.table_data = TableData(table_def, getattr(self,'alias', ''))
    @property
    def table_name(self)->str:
        return self.table_data.table_name
    @property
    def table_def(self)->TableDefinition:
        return self.table_data.table_def
    def _get_parse_flags(self):
        return [SQLFlags.ALIAS]
    def _get_parameters(self):
        return None        

class SQLselect(SQLselectBase):
    def __init__(self, table_def: TableDefinition, **args):
        self.table_data = TableData(table_def)
        super().__init__(**args)    
    def _all_columns(self)->bool:
        return not self.arg_columns or self.arg_columns == []
    def _get_name(self):
        result = self.table_data.table_name
        if self.joins:
            result = result + ',' + ','.join([join for join in self.joins])
        return result

class SQLcreateTable(SQLTablebase):
    def __create_index_str(self, index: IndexDefinition)->str:
        result = 'CREATE '
        if index.is_unique():
            result = result + 'UNIQUE '
        result = result + f'INDEX IF NOT EXISTS {index.name} ON {self.table_name}(' + ','.join([column for column in index.columns])
        return result
    def _get_query(self):
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
        if _nothing_to_do(self.table_def.columns):
            return ''
        result = f'CREATE TABLE IF NOT EXISTS {self.table_name} ({",".join([column_string(column) for column in self.table_def.columns])}' 
        if self.table_def.is_compound_primary():
            result = result + f',PRIMARY KEY({",".join([column.name for column in self.columns if column.is_primary()])})'
        if self.table_def.has_foreign_keys():
            result  = result + ',' + ','.join([f'FOREIGN KEY({key.column_name}) REFERENCES {key.ref_table}({key.ref_column}){key.action_str()}' for key in self.table_def.foreign_keys])
        if self.table_def.has_index():
            result  = result + ');\n' + ');\n'.join([self.__create_index_str(index) for index in self.table_def.indexes])
#            result  = result + ',' + ','.join([str(key) for key in self.table_def.foreign_keys])
#        return f'FOREIGN KEY: {self.column_name} references {self.ref_table}.{self.ref_column}' + ondelete_str + onupdate_str
        return result + ');'

class SQLdropTable(SQLTablebase):
    def _get_query(self):
        return f'DROP TABLE IF EXISTS {self.table_name};'

class SQLinsert(SQLTablebase):
    def _get_parse_flags(self):
        return [SQLFlags.COLUMNS, SQLFlags.VALUES]
    def _get_query(self):
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
    def _get_parameters(self):
        return self.values

class SQLupdate(SQLTablebase):
    def _get_parse_flags(self):
        return [SQLFlags.COLUMNS, SQLFlags.WHERE, SQLFlags.VALUES]
    def _get_query(self):
        result = f'UPDATE {self.table_name} SET ' + ','.join([f'{column}=?' for column in self.arg_columns])
        if self.where_expression:
            result = result + '\nWHERE ' + self.where_expression.parametrized
        return result + ';'
    def _get_parameters(self):
        if self.where_expression:
            return [*self.values, *self.where_expression.parameters]
        else:
            return self.values

class SQLdelete(SQLTablebase):
    def _get_parse_flags(self):
        return [SQLFlags.WHERE, SQLFlags.VALUES]
    def _get_query(self):
        result = f'DELETE FROM {self.table_name}'
        if self.where_expression:
            result = result + '\nWHERE ' + self.where_expression.parametrized
        return result + ';'
    def _get_parameters(self):
        if self.where_expression:
            return [*self.values, *self.where_expression.parameters]
        else:
            return self.values
