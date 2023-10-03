from __future__ import annotations
import sqlite3 as sql3
import database.dbConst as dbc
from database.tabledef import TableDefinition
from database.SQL import SQLbase, SQLcreate, SQLdelete, SQLdrop, SQLcreate, SQLinsert, SQLselect, SQLupdate
from database.sqlexpr import Ops, SQLexpression as SQE
from general.fileutil import file_exists
from general.log import log_debug, log_error, log_info

class DatabaseException(Exception): pass

class SchemaTableDef(TableDefinition):
    def __init__(self):
        super().__init__('sqlite_schema')
        self.add_column('type',dbc.TEXT)
        self.add_column('name',dbc.TEXT)
        self.add_column('tbl_name',dbc.TEXT)
        self.add_column('rootpage',dbc.INTEGER)
        self.add_column('sql', dbc.TEXT)

def one_line(value: str)->str:
    return value.replace('\n', ' ')
class Database:
    def __init__(self, filename: str, _reset_flag = False):
        if not _reset_flag and not file_exists(filename):
            log_error(f'Database {filename} niet gevonden.')
            return None
        self.raise_error = True
        self._reset_flag = _reset_flag
        self._commit_level = 0
        self.connection = None
        try:
            self.connection = self.open_database(filename)
            if not self.connection:
                raise DatabaseException('Connectie niet geopend')
            self.log_info('database logging started...') 
            self.log_info(f'connection ({filename}) opened...')
            self.connection.row_factory = sql3.Row
            self.enable_foreign_keys()
        except Exception as E:
            log_error(f'Kan database {filename} niet initialiseren:\n\t{E}')
    @classmethod
    def create_from_schema(cls, schema: Schema, filename: str):  
        result = cls(filename, _reset_flag = True)  
        if result and result.connection:
            result.__clear()        
            result._reset_flag = False
            log_info('Start reading and creating schema')
            for table in schema.tables():
                result.create_table(table)
                log_info('End reading and creating schema')
            return result
        else:
            # log_error(f'Kan database {filename} niet initialiseren...') is waarschijnlijk al gemeld
            return None           
    def __clear(self):
        try:
            schema = Schema.read_from_database(self)
            self.disable_foreign_keys()
            for table in schema.tables():
                self.drop_table(table)
            self.commit()
        finally:
            self.enable_foreign_keys()
            pass
    def log_info(self, str):
        log_info(f'DB:{one_line(str)}')
    def log_error(self, str):
        log_error(str)
    def close(self):
        self.commit()
        self.connection.close()
        self.log_info('connection closed...')
    def enable_foreign_keys(self):
        self._execute_sql_command('pragma foreign_keys=ON')
    def disable_foreign_keys(self):
        self._execute_sql_command('pragma foreign_keys=OFF')
    def open_database(self, filename):
        try:
            conn = sql3.connect(filename)#, isolation_level=None)
            return conn
        except sql3.Error as e:
            self.log_error(f'SQLITE error: {str(e)}')
            if self.raise_error:
                raise e
            return None
    def _execute_sql_command(self, string, parameters=None, return_values=False):
        try:
            c = self.connection.cursor()
            if parameters:
                self.log_info(f'{string} {parameters}')
                c.execute('' + string + '', parameters)
            else:
                self.log_info(string)
                c.execute('' + string + '')
            if return_values:
                return c.fetchall()
        except sql3.Error as e:
            self.log_error('***ERROR***: '+str(e))
            if self.raise_error:
                raise e
        return None
    def execute_sql_command(self, sql:SQLbase):        
        self._execute_sql_command(sql.Query, sql.Parameters)
    def execute_select(self, sql:SQLselect):
        return self._execute_sql_command(sql.Query, sql.Parameters, True)
    def commit(self):
        if self._commit_level > 0:
            log_debug(f'Committing (level: {self._commit_level})')
            return
        self.log_info('Committing')
        self.connection.commit()
    def disable_commit(self):
        self._commit_level += 1
    def enable_commit(self):
        self._commit_level -= 1
    #note: SQLite savepoints do not work as expected in python
    def rollback(self):
        self.log_info('Rolling back')
        self.connection.rollback()
    def create_table(self, tabledef):
        sql = SQLcreate(tabledef)
        self.execute_sql_command(sql)
    def drop_table(self, tabledef):
        sql = SQLdrop(tabledef)
        self.execute_sql_command(sql)
    def create_record(self, tabledef, **args):
        sql = SQLinsert(tabledef, **args)
        self.execute_sql_command(sql)
    def read_record(self, tabledef, **args):
        sql = SQLselect(tabledef, **args)        
        return self.execute_select(sql)
    def update_record(self, tabledef, **args):
        sql = SQLupdate(tabledef, **args)
        self.execute_sql_command(sql)
    def delete_record(self, tabledef, **args):
        sql = SQLdelete(tabledef, **args)
        self.execute_sql_command(sql)

class Schema:
    def __init__(self):
        self.__tables = {}
    def add_table(self, table: TableDefinition):
        self.__tables[table.name] = table
    def table(self, table_name: str)->TableDefinition:
        return self.__tables.get(table_name, None)
    def tables(self):
        return self.__tables.values()
    @classmethod
    def read_from_database(cls, database: Database):
        def create_table_definition(table_name, columns_from_pragma, foreign_keys_from_pragma):
            table = TableDefinition(table_name)
            for column in columns_from_pragma:
                (col_cid, col_name, col_type, col_notnull, col_dflt_value, col_pk) = column
                args_dict = {}
                if col_pk:
                    args_dict['primary'] = True
                if col_notnull:
                    args_dict['notnull'] = True
                if col_dflt_value:
                    args_dict['default_value'] = col_dflt_value        
                table.add_column(col_name, col_type, **args_dict)
            for key in foreign_keys_from_pragma:
                (key_id, key_seq, foreign_table_name, local_column_name, foreign_column_name, on_update, on_delete, match) = key
                table.add_foreign_key(local_column_name, foreign_table_name, foreign_column_name, onupdate=on_update, ondelete=on_delete)
            return table  
        result = Schema()
        schema_table_def = SchemaTableDef()
        sql = SQLselect(schema_table_def, columns=['name'], where=SQE('type', Ops.EQ, 'table'))
        for table in database._execute_sql_command(sql.Query, parameters=sql.Parameters, return_values=True):
            columns = database._execute_sql_command(f'pragma table_info({table["name"]})', return_values=True)
            foreign_keys = database._execute_sql_command(f'pragma foreign_key_list({table["name"]})', return_values=True)            
            result.add_table(create_table_definition(table["name"], columns, foreign_keys))
        return result    

