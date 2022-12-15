from database.SQL import SQLselect
from database.database import Database, Schema
from database.tabledef import TableDefinition
from general.log import logInfo

class DatabaseDumper:
    def __init__(self, database: Database):
        self.database = database
        logInfo('Start reading schema from database for dump')
        self.tables = Schema.read_from_database(self.database).tables()         
        logInfo('End reading schema from database for dump')
    def DumpTables(self, tables=[], include_schema = False):
        for table in self.tables:
            if tables == [] or table.table_name in tables:
                self._DumpTable(table, include_schema)
    def DumpTable(self, table_name: str, include_schema = False):        
        for table in self.tables:
            if table.table_name == table_name:
                self._DumpTable(table, include_schema)
    def _DumpTable(self, table: TableDefinition, include_schema = False):
        if include_schema:
            print(table)
        else:
            print(f'{table.table_name.upper()}:')
        logInfo(f'dumping {table.tablename}')
        sql = SQLselect(table)
        for record in self.database._execute_sql_command(sql.Query, parameters=sql.Parameters, return_values=True):
            print(list(record))
        logInfo(f'end dumping {table.tablename}')
