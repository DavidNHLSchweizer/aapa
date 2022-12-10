from database.SQL import SQLselect
from database.database import Database, Schema
from database.tabledef import TableDefinition

class DatabaseDumper:
    def __init__(self, database: Database):
        self.database = database         
    def DumpTables(self):
        schema = Schema.read_from_database(self.database)
        for table in schema.tables():
            self.DumpTable(table)
    def DumpTable(self, table: TableDefinition):
        print(table)
        sql = SQLselect(table)
        for record in self.database._execute_sql_command(sql.Query, parameters=sql.Parameters, return_values=True):
            print(list(record))
