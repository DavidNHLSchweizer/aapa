from database.aapa_database import MijlpaalDirectory_FilesTableDefinition, MijlpaalDirectoryTableDefinition
    
from data.general.const import MijlpaalType
from data.general.detail_rec import DetailRec, DetailRecData
from data.classes.mijlpaal_directories import MijlpaalDirectory
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.mappers import ColumnMapper, FilenameColumnMapper, TimeColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.extended_crud import ExtendedCRUD
from storage.general.CRUDs import register_crud
from database.classes.database import Database
from database.classes.table_def import TableDefinition

class MijlpaalDirectoryTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'datum': return TimeColumnMapper(column_name)
            case 'directory': return FilenameColumnMapper(column_name)
            case 'mijlpaal_type': return ColumnMapper(column_name, db_to_obj=MijlpaalType)
            case _: return super()._init_column_mapper(column_name, database)


class MijlpaalDirectoriesDetailRec(DetailRec): pass
class MijlpaalDirectoriesFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'mp_dir_id','file_id')

register_crud(class_type=MijlpaalDirectory, 
                table=MijlpaalDirectoryTableDefinition(), 
                crud=ExtendedCRUD,     
                mapper_type=MijlpaalDirectoryTableMapper, 
                details_data=
                    [DetailRecData(aggregator_name='files', detail_aggregator_key='files', 
                                   detail_rec_type=MijlpaalDirectoriesDetailRec),
                    ]
                )
register_crud(class_type=MijlpaalDirectoriesDetailRec, 
                table=MijlpaalDirectory_FilesTableDefinition(), 
                mapper_type=MijlpaalDirectoriesFilesTableMapper, 
                autoID=False,
                main=False
                )


