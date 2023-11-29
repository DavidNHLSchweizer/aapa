from __future__ import annotations
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog
from data.classes.detail_rec import DetailRec, DetailRecData
from data.storage.detail_rec import DetailRecStorage, DetailsRecTableMapper
from data.storage.general.mappers import BoolColumnMapper, ColumnMapper, TableMapper, TimeColumnMapper
from data.storage.table_registry import register_table
from data.storage.storage_base import StorageBase
from database.database import Database
from database.dbConst import EMPTY_ID
from database.table_def import TableDefinition
from general.log import log_warning

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'

class ActionlogAanvragenDetailRec(DetailRec): pass
class ActionlogAanvragenTableMapper(DetailsRecTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id','aanvraag_id')

class ActionlogInvalidFilesDetailRec(DetailRec): pass
class ActionlogInvalidFilesTableMapper(DetailsRecTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table,  class_type, 'log_id','file_id')

class ActionlogTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'date': return TimeColumnMapper(column_name)
            case 'can_undo': return BoolColumnMapper(column_name)
            case 'action': return ColumnMapper(column_name=column_name, db_to_obj=ActionLog.Action)
            case _: return super()._init_column_mapper(column_name, database)

class ActionlogStorage(StorageBase):
    # def __init__(self, database: Database):
    #     super().__init__(database, class_type=ActionLog)
    def _find_action_log(self, id: int = EMPTY_ID)->ActionLog:
        if id == EMPTY_ID:
            # id = self.query_builder.find_max_id()
            qb = self.query_builder
            id = qb.find_max_value('id', where = qb.build_where_from_values(column_names=['can_undo'], values=[True]))
        if id is None or id == EMPTY_ID:
            log_warning(NoUNDOwarning)
            return None
        return self.read(id)
    def last_action(self)->ActionLog:
        return self._find_action_log()

action_log_table = ActionLogTableDefinition()
register_table(class_type=ActionLog, table=action_log_table, 
               mapper_type=ActionlogTableMapper, 
               crud=ActionlogStorage,
                details_data=
                    [
                        DetailRecData(aggregator_name='_data', detail_aggregator_key='aanvragen', 
                                   detail_rec_type=ActionlogAanvragenDetailRec),
                        DetailRecData(aggregator_name='_data', detail_aggregator_key='invalid_files', 
                                   detail_rec_type=ActionlogInvalidFilesDetailRec),
                    ],
               autoID=True)
register_table(class_type=ActionlogAanvragenDetailRec, table=ActionLogAanvragenTableDefinition(),
               crud=DetailRecStorage,
                    mapper_type=ActionlogAanvragenTableMapper)
register_table(class_type=ActionlogInvalidFilesDetailRec, table=ActionLogFilesTableDefinition(), 
               crud=DetailRecStorage,
                    mapper_type=ActionlogInvalidFilesTableMapper)