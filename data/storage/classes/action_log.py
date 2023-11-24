from __future__ import annotations
from typing import Any
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog, ActionLogAggregator
from data.storage.mappers import BoolColumnMapper, ColumnMapper, TableMapper, TimeColumnMapper
from data.storage.storage_const import DBtype, DetailRec
from data.storage.table_registry import CRUD_AggregatorData, register_table
from data.storage.storage_base import StorageBase
from database.database import Database
from database.dbConst import EMPTY_ID
from database.table_def import TableDefinition
from general.log import log_warning

NoUNDOwarning = 'Geen ongedaan te maken acties opgeslagen in database.'

class DetailsRecTableMapper(TableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec], 
                 main_key: str, detail_key:str):
        super().__init__(database, table, class_type)
        self.main_key = main_key
        self.detail_key=detail_key
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'main_key': return ColumnMapper(column_name,attribute_name=self.main_key)
            case 'detail_key': return ColumnMapper(column_name,attribute_name=self.detail_key)
            case  _: super()._init_column_mapper(column_name, database)

class ActionlogAanvragenDetailRec(DetailRec): pass
class ActionlogAanvragenTableMapper(DetailsRecTableMapper):
    def __init__(self, database: Database):
        super().__init__(database, ActionLogAanvragenTableDefinition(), ActionlogAanvragenDetailRec, 'log_id','aanvraag_id')

class ActionlogInvalidFilesDetailRec(DetailRec): pass
class ActionlogInvalidFilesTableMapper(DetailsRecTableMapper):
    def __init__(self, database: Database):
        super().__init__(database, ActionLogAanvragenTableDefinition(), ActionlogInvalidFilesDetailRec, 'log_id','files_id')

class ActionLogActionColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return ActionLog.Action(db_value)

class ActionlogTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'date': return TimeColumnMapper(column_name)
            case 'can_undo': return BoolColumnMapper(column_name)
            case 'action': return ActionLogActionColumnMapper(column_name)
            case _: return super()._init_column_mapper(column_name, database)

class ActionlogStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, ActionLog, autoID=True)   
    def _find_action_log(self, id: int = EMPTY_ID)->ActionLog:
        if id != EMPTY_ID:
            id = self.query_builder.find_max_id()[0]
            # # if (row := self.database._execute_sql_command(f'select id from {self.table_name} where can_undo = ? group by can_undo having max(id)', [1], True)):
            #     id = row[0][0]
        if id is None or id == EMPTY_ID:
            log_warning(NoUNDOwarning)
            return None
        return self.read(id)
    def last_action(self)->ActionLog:
        return self._find_action_log()
   # # def add_details(self, action_log: ActionLog, crud_details: CRUDbaseDetails, crud_table: CRUDbase):
    #     for record in crud_details.read(action_log.id):
    #         action_log.add(crud_table.read(record.detail_key))

action_log_table = ActionLogTableDefinition()
register_table(class_type=ActionLog, table=action_log_table, mapper_type=ActionlogTableMapper, autoID=True)
register_table(class_type=ActionlogAanvragenDetailRec, table=ActionLogAanvragenTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), 
                                            attribute='aanvragen'), mapper_type=ActionlogAanvragenTableMapper)
register_table(class_type=ActionlogInvalidFilesDetailRec, table=ActionLogFilesTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), 
                                                 attribute='invalid_files'), mapper_type=ActionlogInvalidFilesTableMapper)