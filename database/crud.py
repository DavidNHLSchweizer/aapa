from database.database import Database
from database.tabledef import TableDefinition

class CRUDbase:
    def __init__(self, database: Database, table: TableDefinition):
        self.database = database
        self.table = table
    def create(self, **kwargs):
        self.database.create_record(self.table, **kwargs)
    def read(self, **kwargs):
        if row := self.database.read_record(self.table, **kwargs):
            return row[0]
        else:
            return None 
    def update(self, **kwargs):
        self.database.update_record(self.table, **kwargs)
    def delete(self, **kwargs):
        self.database.delete_record(self.table, **kwargs)
