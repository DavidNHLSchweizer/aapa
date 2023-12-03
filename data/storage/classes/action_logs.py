from __future__ import annotations
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_logs  import ActionLog
from data.classes.detail_rec import DetailRec, DetailRecData
from data.storage.CRUDs import register_crud
from data.storage.detail_rec_crud import DetailRecsTableMapper
from data.storage.general.mappers import BoolColumnMapper, ColumnMapper, TableMapper, TimeColumnMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.queries.action_logs import ActionLogQueries
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_warning

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'

class ActionLogAanvragenDetailRec(DetailRec): pass
class ActionlogAanvragenTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id','aanvraag_id')

class ActionLogInvalidFilesDetailRec(DetailRec): pass
class ActionlogInvalidFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id','file_id')

class ActionLogTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'date': return TimeColumnMapper(column_name)
            case 'can_undo': return BoolColumnMapper(column_name)
            case 'action': return ColumnMapper(column_name=column_name, db_to_obj=ActionLog.Action)
            case _: return super()._init_column_mapper(column_name, database)

action_log_table = ActionLogTableDefinition()
register_crud(class_type=ActionLog, 
                table=action_log_table, 
                mapper_type=ActionLogTableMapper, 
                crud=ExtendedCRUD,
                queries_type=ActionLogQueries,
                details_data=
                    [
                        DetailRecData(aggregator_name='_data', detail_aggregator_key='aanvragen', 
                                   detail_rec_type=ActionLogAanvragenDetailRec),
                        DetailRecData(aggregator_name='_data', detail_aggregator_key='invalid_files', 
                                   detail_rec_type=ActionLogInvalidFilesDetailRec),
                    ]
                )
register_crud(class_type=ActionLogAanvragenDetailRec, 
                table=ActionLogAanvragenTableDefinition(),
                mapper_type=ActionlogAanvragenTableMapper, 
                autoID=False, 
                main=False)
register_crud(class_type=ActionLogInvalidFilesDetailRec, 
                table=ActionLogFilesTableDefinition(), 
                mapper_type=ActionlogInvalidFilesTableMapper, 
                autoID=False,
                main=False)