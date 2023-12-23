from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.storage.CRUDs import register_crud
from data.classes.mappers import ColumnMapper
from data.storage.general.table_mapper import TableMapper
from data.storage.queries.studenten import StudentQueries
from database.database import Database

class StudentenTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Student.Status)
            case _: return super()._init_column_mapper(column_name, database)

register_crud(class_type=Student, 
                table=StudentTableDefinition(),
                mapper_type=StudentenTableMapper,
                queries_type=StudentQueries
                )