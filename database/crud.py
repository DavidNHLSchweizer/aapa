from database.database import Database
from database.tabledef import TableDefinition

class CRUDbase:
    def __init__(self, database: Database, table: TableDefinition):
        self.database = database
        self.table = table
    def create(self, **kwargs):
        self.database.create_record(self.table, **kwargs)
    def read(self, **kwargs):
        multiple = kwargs.pop('multiple', False)
        if rows := self.database.read_record(self.table, **kwargs):
            if multiple:
                return rows
            else:
                return rows[0]
        return None 
    def update(self, **kwargs):
        self.database.update_record(self.table, **kwargs)
    def delete(self, **kwargs):
        self.database.delete_record(self.table, **kwargs)
