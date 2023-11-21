from __future__ import annotations
from typing import Any
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog, ActionLogAggregator
from data.crud.aanvragen import CRUD_aanvragen

from data.crud.mappers import BoolColumnMapper, ColumnMapper, TableMapper, TimeColumnMapper
from data.crud.aggregator import CRUD_Aggregator
from data.crud.crud_base import CRUD,  CRUD_AggregatorData, CRUDbase
from data.crud.crud_const import DBtype, DetailRec
from data.crud.files import CRUD_files
from data.storage.crud_factory import registerCRUD
from data.storage.storage_base import StorageBase

class ActionAanvragenDetailRec(DetailRec): pass
class ActionlogStorage(StorageBase):
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_attribute('main_key', 'log_id')
        mapper.set_attribute('detail_key', 'aanvraag_id')

class ActionInvalidFilesDetailRec(DetailRec): pass
class CRUD_action_log_invalid_files(CRUD_Aggregator): 
    def customize_mapper(self):
        self.mapper.set_attribute('main_key', 'log_id')
        self.mapper.set_attribute('detail_key', 'file_id')
    # # def __init__(self, database: Database):
    # #     super().__init__(CRUD_action_log(database), ActionLogFilesTableDefinition())
    # def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
    #     return action_log.invalid_files

class ActionLogActionColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return ActionLog.Action(db_value)

class CRUD_action_log(CRUDbase):
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_mapper(TimeColumnMapper('date'))
        mapper.set_mapper(BoolColumnMapper('can_undo'))
        mapper.set_mapper(ActionLogActionColumnMapper('action'))
   # # def add_details(self, action_log: ActionLog, crud_details: CRUDbaseDetails, crud_table: CRUDbase):
    #     for record in crud_details.read(action_log.id):
    #         action_log.add(crud_table.read(record.detail_key))
action_log_table = ActionLogTableDefinition()
registerCRUD(class_type=ActionLog, table=action_log_table, autoID=True)
registerCRUD(class_type=ActionAanvragenDetailRec, table=ActionLogAanvragenTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), attribute='aanvragen'))
registerCRUD(class_type=ActionInvalidFilesDetailRec, table=ActionLogFilesTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), attribute='invalid_files'))