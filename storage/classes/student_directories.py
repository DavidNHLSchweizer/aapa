from database.aapa_database import StudentDirectory_DirectoriesTableDefinition, StudentDirectoryTableDefinition
from data.classes.base_dirs import BaseDir
from data.general.detail_rec import DetailRec, DetailRecData
from storage.general.mappers import ColumnMapper, FilenameColumnMapper
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from storage.general.CRUDs import CRUDColumnMapper, create_crud, register_crud
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.extended_crud import ExtendedCRUD
from storage.general.table_mapper import TableMapper
from storage.queries.student_directories import StudentDirectoryQueries
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

class StudentDirectoriesDirectoriesDetailRec(DetailRec): pass
class StudentDirectoriesDirectoriesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'stud_dir_id','mp_dir_id')

register_crud(class_type=StudentDirectory, 
                table=StudentDirectoryTableDefinition(), 
                crud=ExtendedCRUD,     
                mapper_type=StudentDirectoriesTableMapper, 
                queries_type=StudentDirectoryQueries,
                details_data=
                    [DetailRecData(aggregator_name='data', detail_aggregator_key='directories', 
                                   detail_rec_type=StudentDirectoriesDirectoriesDetailRec),
                    ]
                )

register_crud(class_type=StudentDirectoriesDirectoriesDetailRec, 
                table=StudentDirectory_DirectoriesTableDefinition(), 
                mapper_type=StudentDirectoriesDirectoriesTableMapper, 
                autoID=False,
                main=False
                )

