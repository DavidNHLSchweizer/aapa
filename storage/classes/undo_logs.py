from __future__ import annotations
from database.aapa_database import UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, UndoLogTableDefinition
from data.classes.undo_logs  import UndoLog
from data.general.detail_rec import DetailRec, DetailRecData
from storage.general.CRUDs import register_crud
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.mappers import BoolColumnMapper, ColumnMapper, TimeColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.extended_crud import ExtendedCRUD
from storage.queries.undo_logs import UndoLogQueries
from database.classes.database import Database
from database.classes.table_def import TableDefinition

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'

class UndoLogAanvragenDetailRec(DetailRec): pass
class UndoLogAanvragenTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id','aanvraag_id')

class UndoLogFilesDetailRec(DetailRec): pass
class UndoLogFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id','file_id')

class UndoLogTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'date': return TimeColumnMapper(column_name)
            case 'can_undo': return BoolColumnMapper(column_name)
            case 'action': return ColumnMapper(column_name=column_name, db_to_obj=UndoLog.Action)
            case _: return super()._init_column_mapper(column_name, database)

undo_log_table = UndoLogTableDefinition()
register_crud(class_type=UndoLog, 
                table=undo_log_table, 
                mapper_type=UndoLogTableMapper, 
                crud=ExtendedCRUD,
                queries_type=UndoLogQueries,
                details_data=
                    [
                        DetailRecData(aggregator_name='data', detail_aggregator_key='aanvragen', 
                                   detail_rec_type=UndoLogAanvragenDetailRec),
                        DetailRecData(aggregator_name='data', detail_aggregator_key='invalid_files', 
                                   detail_rec_type=UndoLogFilesDetailRec),
                    ]
                )
register_crud(class_type=UndoLogAanvragenDetailRec, 
                table=UndoLogAanvragenTableDefinition(),
                mapper_type=UndoLogAanvragenTableMapper, 
                autoID=False, 
                main=False)
register_crud(class_type=UndoLogFilesDetailRec, 
                table=UndoLogFilesTableDefinition(), 
                mapper_type=UndoLogFilesTableMapper, 
                autoID=False,
                main=False)