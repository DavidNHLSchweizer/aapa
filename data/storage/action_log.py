from __future__ import annotations
from typing import Any
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog, ActionLogAggregator
from data.storage.mappers import BoolColumnMapper, ColumnMapper, TableMapper, TimeColumnMapper
from data.storage.storage_const import DBtype, DetailRec
from data.storage.table_registry import CRUD_AggregatorData, register_table
from data.storage.storage_base import StorageBase
from database.database import Database

class ActionAanvragenDetailRec(DetailRec): pass
class ActionlogStorage(StorageBase):
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_attribute('main_key', 'log_id')
        mapper.set_attribute('detail_key', 'aanvraag_id')

class ActionInvalidFilesDetailRec(DetailRec): pass
class CRUD_action_log_invalid_files(CRUD_AggregatorData):
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_attribute('main_key', 'log_id')
        mapper.set_attribute('detail_key', 'file_id')
    # # def __init__(self, database: Database):
    # #     super().__init__(CRUD_action_log(database), ActionLogFilesTableDefinition())
    # def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
    #     return action_log.invalid_files

class ActionLogActionColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return ActionLog.Action(db_value)

class ActionlogStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, ActionLog, autoID=True)   
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_mapper(TimeColumnMapper('date'))
        mapper.set_mapper(BoolColumnMapper('can_undo'))
        mapper.set_mapper(ActionLogActionColumnMapper('action'))
   # # def add_details(self, action_log: ActionLog, crud_details: CRUDbaseDetails, crud_table: CRUDbase):
    #     for record in crud_details.read(action_log.id):
    #         action_log.add(crud_table.read(record.detail_key))

action_log_table = ActionLogTableDefinition()
register_table(class_type=ActionLog, table=action_log_table, autoID=True)
register_table(class_type=ActionAanvragenDetailRec, table=ActionLogAanvragenTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), attribute='aanvragen'))
register_table(class_type=ActionInvalidFilesDetailRec, table=ActionLogFilesTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), attribute='invalid_files'))