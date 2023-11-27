import sqlite3 as sql3
from typing import Any
from database.database import Database, Schema
from database.sql_table import SQLselect
from database.table_def import TableDefinition
from general.log import log_info

class DatabaseDumper:
    def __init__(self, database: Database):
        self.database = database
        log_info('Start reading schema from database for dump')
        self.tables = Schema.read_from_database(self.database).tables()         
        log_info('End reading schema from database for dump')
    def DumpTables(self, tables=[], include_schema = False):
        for table in self.tables:
            if tables == [] or table.table_name in tables:
                self._DumpTable(table, include_schema)
    def DumpTable(self, table_name: str, include_schema = False):        
        for table in self.tables:
            if table.table_name == table_name:
                self._DumpTable(table, include_schema)
    @staticmethod
    def convert_row(row: sql3.Row)->list[Any]:
        return [row[key] for key in row.keys()]

    def _DumpTable(self, table: TableDefinition, include_schema = False):
        if include_schema:
            print(table)
        else:
            print(f'{table.name.upper()}:')
        log_info(f'dumping {table.tablename}')
        sql = SQLselect(table)
        for record in self.database._execute_sql_command(sql.query, parameters=sql.parameters, return_values=True):
            print(DatabaseDumper.convert_row(record))
        log_info(f'end dumping {table.tablename}')
