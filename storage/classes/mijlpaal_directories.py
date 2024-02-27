from data.general.details_record import DetailsRecord
from database.aapa_database import MijlpaalDirectoryDetailsTableDefinition, MijlpaalDirectoriesTableDefinition
    
from data.general.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from storage.general.details_crud import DetailsRecordTableMapper
from storage.general.mappers import ColumnMapper, FilenameColumnMapper, TimeColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.aggregator_crud import AggregatorCRUD
from storage.general.CRUDs import register_crud
from database.classes.database import Database
from database.classes.table_def import TableDefinition
from storage.queries.mijlpaal_directories import MijlpaalDirectoriesQueries

class MijlpaalDirectoriesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'datum': return TimeColumnMapper(column_name)
            case 'directory': return FilenameColumnMapper(column_name)
            case 'mijlpaal_type': return ColumnMapper(column_name, db_to_obj=MijlpaalType)
            case _: return super()._init_column_mapper(column_name, database)


class MijlpaalDirectoryDetailsRecord(DetailsRecord): pass
class MijlpaalDirectoryDetailsTableMapper(DetailsRecordTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: DetailsRecord):
        super().__init__(database, table, class_type, 'mp_dir_id')

register_crud(class_type=MijlpaalDirectory, 
                table=MijlpaalDirectoriesTableDefinition(), 
                crud=AggregatorCRUD,     
                mapper_type=MijlpaalDirectoriesTableMapper, 
                queries_type=MijlpaalDirectoriesQueries,
                details_record_type=MijlpaalDirectoryDetailsRecord,
                )
register_crud(class_type=MijlpaalDirectoryDetailsRecord, 
                table=MijlpaalDirectoryDetailsTableDefinition(), 
                mapper_type=MijlpaalDirectoryDetailsTableMapper, 
                autoID=False,
                main=False
                )


