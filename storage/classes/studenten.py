from database.aapa_database import StudentenTableDefinition
from data.classes.studenten import Student
from storage.general.CRUDs import register_crud
from storage.general.mappers import ColumnMapper
from storage.general.table_mapper import TableMapper
from storage.queries.studenten import StudentenQueries
from database.classes.database import Database

class StudentenTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Student.Status)
            case _: return super()._init_column_mapper(column_name, database)

register_crud(class_type=Student, 
                table=StudentenTableDefinition(),
                mapper_type=StudentenTableMapper,
                queries_type=StudentenQueries
                )