from data.aapa_database import StudentDirectoryAanvragenTableDefinition, StudentDirectoryTableDefinition, StudentDirectoryVerslagenTableDefinition
from data.classes.base_dirs import BaseDir
from data.classes.detail_rec import DetailRec, DetailRecData
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.storage.CRUDs import CRUDColumnMapper, create_crud, register_crud
from data.storage.detail_rec_crud import DetailRecsTableMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper, TableMapper
from database.database import Database
from database.table_def import TableDefinition

class StudentDirectoriesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case 'stud_id': 
                return CRUDColumnMapper(column_name, attribute_name='student', crud=create_crud(database, Student))
            case 'basedir_id': 
                return CRUDColumnMapper(column_name=column_name, attribute_name='base_dir', crud=create_crud(database, BaseDir))
            case _: return super()._init_column_mapper(column_name, database)

class StudentDirectoriesAanvragenDetailRec(DetailRec): pass
class StudentDirectoriesAanvragenTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'stud_dir_id','aanvraag_id')

class StudentDirectoriesVerslagenDetailRec(DetailRec): pass
class StudentDirectoriesVerslagenTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'stud_dir_id','verslag_id')

register_crud(class_type=StudentDirectory, 
                table=StudentDirectoryTableDefinition(), 
                crud=ExtendedCRUD,     
                # queries_type=AanvraagQueries,        
                mapper_type=StudentDirectoriesTableMapper, 
                details_data=
                    [DetailRecData(aggregator_name='data', detail_aggregator_key='aanvragen', 
                                   detail_rec_type=StudentDirectoriesAanvragenDetailRec),
                    DetailRecData(aggregator_name='data', detail_aggregator_key='verslagen', 
                                   detail_rec_type=StudentDirectoriesVerslagenDetailRec),
                    ]
                )
register_crud(class_type=StudentDirectoriesAanvragenDetailRec, 
                table=StudentDirectoryAanvragenTableDefinition(), 
                mapper_type=StudentDirectoriesAanvragenTableMapper, 
                autoID=False,
                main=False
                )

register_crud(class_type=StudentDirectoriesVerslagenDetailRec, 
                table=StudentDirectoryVerslagenTableDefinition(), 
                mapper_type=StudentDirectoriesVerslagenTableMapper, 
                autoID=False,
                main=False
                )

