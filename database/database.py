from __future__ import annotations
from contextlib import contextmanager
import sqlite3 as sql3
import database.dbConst as dbc
from database.tabledef import TableDefinition
from database.viewdef import SQLcreateView, SQLdropView, ViewDefinition

from database.SQL import SQLTablebase, SQLcreate, SQLdelete, SQLdrop, SQLcreate, SQLinsert, SQLselect, SQLupdate
from database.sqlexpr import Ops, SQLexpression as SQE
from general.fileutil import file_exists
from general.log import log_debug, log_error, log_exception, log_info

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
        self._foreign_key_level = 0
        self.connection = None
        try:
            self.connection = self.open_database(filename)
            if not self.connection:
                log_exception('Connectie niet geopend', DatabaseException)
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
            with result.pause_foreign_keys():
                for table in schema.tables():
                    result.create_table(table)
                for view in schema.views():
                    result.create_view(view)                
            log_info('End reading and creating schema')
            return result
        else:
            # log_error(f'Kan database {filename} niet initialiseren...') is waarschijnlijk al gemeld
            return None           
    def __clear(self):
        schema = Schema.read_from_database(self)
        with self.pause_foreign_keys():
            for table in schema.tables():
                self.drop_table(table)
            for view in schema.views():
                self.drop_view(view)
            self.commit()
    def log_info(self, str):
        log_info(f'DB:{one_line(str)}')
    def log_error(self, str):
        log_error(str)
    def close(self):
        self.commit()
        self.connection.close()
        self.log_info('connection closed...')
    def enable_foreign_keys(self):
        self._foreign_key_level -= 1
        if self._foreign_key_level == 0:
            self._execute_sql_command('pragma foreign_keys=ON')
    def disable_foreign_keys(self):
        if self._foreign_key_level == 0:
            self._execute_sql_command('pragma foreign_keys=OFF')
        self._foreign_key_level += 1
    @contextmanager
    def pause_foreign_keys(self):
        self.disable_foreign_keys()
        yield
        self.enable_foreign_keys()
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
    def execute_sql_command(self, sql:SQLTablebase):        
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
    def create_view(self, viewdef: ViewDefinition):
        sql = SQLcreateView(viewdef)
        self.execute_sql_command(sql)
    def drop_table(self, tabledef):
        sql = SQLdrop(tabledef)
        self.execute_sql_command(sql)
    def drop_view(self, viewdef):
        sql = SQLdropView(viewdef)
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
        self.__views = {}
    def add_table(self, table: TableDefinition):
        self.__tables[table.name] = table
    def add_view(self, view: ViewDefinition):
        self.__views[view.name] = view
    def table(self, table_name: str)->TableDefinition:
        return self.__tables.get(table_name, None)
    def tables(self)->list[TableDefinition]:
        return self.__tables.values()
    def views(self)->list[ViewDefinition]:
        return self.__views.values()
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
        def create_view_definition(view_name, columns_from_pragma, sql):
            column_names = [column['name'] for column in columns_from_pragma]
            # print(column_names)
            # print(sql[sql.find('AS SELECT')+3:])
            return ViewDefinition(view_name, column_names=column_names, query=sql[sql.find('AS SELECT')+3:])
        result = Schema()
        schema_table_def = SchemaTableDef()
        sql = SQLselect(schema_table_def, columns=['name'], where=SQE('type', Ops.EQ, 'table'))
        for table in database._execute_sql_command(sql.Query, parameters=sql.Parameters, return_values=True):
            columns = database._execute_sql_command(f'pragma table_info({table["name"]})', return_values=True)
            foreign_keys = database._execute_sql_command(f'pragma foreign_key_list({table["name"]})', return_values=True)            
            result.add_table(create_table_definition(table["name"], columns, foreign_keys))       
        sql = SQLselect(schema_table_def, columns=['name', 'sql'], where=SQE('type', Ops.EQ, 'view'))
        for view in database._execute_sql_command(sql.Query, parameters=sql.Parameters, return_values=True):
            columns = database._execute_sql_command(f'pragma table_info({view["name"]})', return_values=True)
            result.add_view(create_view_definition(view["name"], columns, view["sql"]))   
        return result    

