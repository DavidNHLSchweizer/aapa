from __future__ import annotations
from data.general.detail_rec2 import DetailRec2, DetailRecData2
from database.aapa_database import UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, UndoLogTableDefinition, UndoLogVerslagenTableDefinition, UndologsDetailsTableDefinition
from data.classes.undo_logs  import UndoLog
from data.general.detail_rec import DetailRec
from main.options import AAPAProcessingOptions
from storage.general.CRUDs import register_crud
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.detail_rec_crud2 import DetailRecsTableMapper2
from storage.general.mappers import BoolColumnMapper, ColumnMapper, TimeColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.extended_crud import ExtendedCRUD
from storage.queries.undo_logs import UndoLogQueries
from database.classes.database import Database
from database.classes.table_def import TableDefinition

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'

class UndoLogDetailRec2(DetailRec2): pass
class UndoLogDetailsTableMapper(DetailRecsTableMapper2):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id')

class UndoLogTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'date': return TimeColumnMapper(column_name)
            case 'can_undo': return BoolColumnMapper(column_name)
            case 'action': return ColumnMapper(column_name=column_name, db_to_obj=UndoLog.Action)
            case 'processing_mode': return ColumnMapper(column_name=column_name, db_to_obj=AAPAProcessingOptions.PROCESSINGMODE)
            case _: return super()._init_column_mapper(column_name, database)

register_crud(class_type=UndoLog, 
                table=UndoLogTableDefinition(), 
                mapper_type=UndoLogTableMapper, 
                crud=ExtendedCRUD,
                queries_type=UndoLogQueries,
                details_data=
                    [
                        DetailRecData2(aggregator_name='data', 
                                   detail_rec_type=UndoLogDetailRec2),
                    ]
                )
register_crud(class_type=UndoLogDetailRec2, 
                table=UndologsDetailsTableDefinition(),
                mapper_type=UndoLogDetailsTableMapper, 
                autoID=False, 
                main=False)
