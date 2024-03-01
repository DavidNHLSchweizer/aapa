from __future__ import annotations
from data.general.details_record import DetailsRecord
from database.aapa_database import UndoLogsTableDefinition, UndologDetailsTableDefinition
from data.classes.undo_logs  import UndoLog
from main.options import AAPAProcessingOptions
from storage.general.CRUDs import register_crud
from storage.general.details_crud import DetailsRecordTableMapper
from storage.general.mappers import BoolColumnMapper, ColumnMapper, TimeColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.aggregator_crud import AggregatorCRUD
from storage.queries.undo_logs import UndoLogsQueries
from database.classes.database import Database
from database.classes.table_def import TableDefinition

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'

class UndoLogDetailsRecord(DetailsRecord): pass
class UndoLogDetailsTableMapper(DetailsRecordTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: DetailsRecord):
        super().__init__(database, table,  class_type, 'log_id')

class UndoLogsTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'date': return TimeColumnMapper(column_name)
            case 'can_undo': return BoolColumnMapper(column_name)
            case 'action': return ColumnMapper(column_name=column_name, db_to_obj=UndoLog.Action)
            case 'processing_mode': return ColumnMapper(column_name=column_name, db_to_obj=AAPAProcessingOptions.PROCESSINGMODE)
            case _: return super()._init_column_mapper(column_name, database)

register_crud(class_type=UndoLog, 
                table=UndoLogsTableDefinition(), 
                mapper_type=UndoLogsTableMapper, 
                crud=AggregatorCRUD,
                queries_type=UndoLogsQueries,
                details_record_type=UndoLogDetailsRecord                    
                )
register_crud(class_type=UndoLogDetailsRecord, 
                table=UndologDetailsTableDefinition(),
                mapper_type=UndoLogDetailsTableMapper, 
                autoID=False, 
                main=False)
