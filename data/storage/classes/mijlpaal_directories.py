from data.aapa_database import MijlpaalDirectory_FilesTableDefinition, MijlpaalDirectoryTableDefinition
    
from data.classes.const import MijlpaalType
from data.classes.detail_rec import DetailRec, DetailRecData
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.storage.detail_rec_crud import DetailRecsTableMapper
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper, TableMapper, TimeColumnMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.CRUDs import register_crud
from database.database import Database
from database.table_def import TableDefinition

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


