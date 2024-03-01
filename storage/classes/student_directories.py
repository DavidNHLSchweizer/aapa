from data.general.details_record import DetailsRecord
from database.aapa_database import StudentDirectoryDetailsTableDefinition, StudentDirectoriesTableDefinition
from data.classes.base_dirs import BaseDir
from storage.general.details_crud import DetailsRecordTableMapper
from storage.general.mappers import ColumnMapper, FilenameColumnMapper
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from storage.general.CRUDs import CRUDColumnMapper, create_crud, register_crud
from storage.general.aggregator_crud import AggregatorCRUD
from storage.general.table_mapper import TableMapper
from storage.queries.student_directories import StudentDirectoriesQueries
from database.classes.database import Database
from database.classes.table_def import TableDefinition

class StudentDirectoriesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case 'stud_id': 
                return CRUDColumnMapper(column_name, attribute_name='student', crud=create_crud(database, Student))
            case 'basedir_id': 
                return CRUDColumnMapper(column_name=column_name, attribute_name='base_dir', crud=create_crud(database, BaseDir))
            case 'status': 
                return ColumnMapper(column_name=column_name, db_to_obj=StudentDirectory.Status)
            case _: return super()._init_column_mapper(column_name, database)

class StudentDirectoryDetailsRecord(DetailsRecord): pass
class StudentDirectoryDetailsTableMapper(DetailsRecordTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: DetailsRecord):
        super().__init__(database, table, class_type, 'stud_dir_id')

register_crud(class_type=StudentDirectory, 
                table=StudentDirectoriesTableDefinition(), 
                crud=AggregatorCRUD,     
                mapper_type=StudentDirectoriesTableMapper, 
                queries_type=StudentDirectoriesQueries,
                details_record_type=StudentDirectoryDetailsRecord,                    
                )

register_crud(class_type=StudentDirectoryDetailsRecord, 
                table=StudentDirectoryDetailsTableDefinition(), 
                mapper_type=StudentDirectoryDetailsTableMapper, 
                autoID=False,
                main=False
                )

