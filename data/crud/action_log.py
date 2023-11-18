from __future__ import annotations
from typing import Any
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog, ActionLogAggregator
from data.crud.aanvragen import CRUD_aanvragen
from data.crud.mappers import BoolColumnMapper, ColumnMapper, TimeColumnMapper
from data.crud.aggregator import CRUD_Aggregator
from data.crud.crud_base import CRUD,  CRUD_AggregatorData, CRUDbase
from data.crud.crud_const import DBtype, DetailRec
from data.crud.crud_factory import registerCRUD
from data.crud.files import CRUD_files

class ActionAanvragenDetailRec(DetailRec): pass
class CRUD_action_log_aanvragen(CRUD_Aggregator):
    def _post_action(self, detail_rec: DetailRec, crud_action: CRUD)->ActionLog:        
        match crud_action:
            case CRUD.INIT:        
                self.mapper.set_attribute('main_key', 'log_id')
                self.mapper.set_attribute('detail_key', 'aanvraag_id')
            case _: pass
        return detail_rec
    # def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, aggregator: AggregatorCRUDdata=None
    #   no_column_ref_for_key = False, autoID=False):)
    # def __init__(self, database: Database, table: TableDefinition, main_crud: CRUDbase, aggregator: Aggregator,  attribute: str):
    # #     super().__init__(CRUD_action_log(database), ActionLogAanvragenTableDefinition())
    # def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
    #     return action_log.aanvragen

class ActionInvalidFilesDetailRec(DetailRec): pass
class CRUD_action_log_invalid_files(CRUD_Aggregator): 
    def _post_action(self, detail_rec: DetailRec, crud_action: CRUD)->ActionLog:        
        match crud_action:
            case CRUD.INIT:        
                self.mapper.set_attribute('main_key', 'log_id')
                self.mapper.set_attribute('detail_key', 'file_id')
            case _: pass
        return detail_rec
    # # def __init__(self, database: Database):
    # #     super().__init__(CRUD_action_log(database), ActionLogFilesTableDefinition())
    # def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
    #     return action_log.invalid_files

class ActionLogActionColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return ActionLog.Action(db_value)

class CRUD_action_log(CRUDbase):
    def _post_action(self, action_log: ActionLog, crud_action: CRUD)->ActionLog:        
        DETAILS = [
                { 'crud_details':CRUD_action_log_aanvragen, 'crud_table': CRUD_aanvragen},
                { 'crud_details':CRUD_action_log_invalid_files, 'crud_table': CRUD_files}
                ]
        match crud_action:
            case CRUD.INIT:        
                self.set_mapper(TimeColumnMapper('date'))
                self.set_mapper(BoolColumnMapper('can_undo'))
                self.set_mapper(ActionLogActionColumnMapper('action'))
                # self.aggregator_CRUD_temp = createCRUD(self.database, ActionAanvragenDetailRec)
        # #adds detail records as needed
        #         # for record in DETAILS:
        #         self.crud_aggregator = CRUD_Aggregator(self.database, ActionLogAggregator())
                    # self.add_details(action_log, record['crud_details'](self.database), record['crud_table'](self.database))            
            case CRUD.CREATE: pass
                # self.crud_aggregator.create(action_log)        

            case _: pass
        return action_log
    # def add_details(self, action_log: ActionLog, crud_details: CRUDbaseDetails, crud_table: CRUDbase):
    #     for record in crud_details.read(action_log.id):
    #         action_log.add(crud_table.read(record.detail_key))
action_log_table = ActionLogTableDefinition()
registerCRUD(CRUD_action_log, class_type=ActionLog, table=action_log_table, autoID=True)
registerCRUD(CRUD_action_log_aanvragen, class_type=ActionAanvragenDetailRec, table=ActionLogAanvragenTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), attribute='aanvragen'))
registerCRUD(CRUD_action_log_invalid_files, class_type=ActionInvalidFilesDetailRec, table=ActionLogFilesTableDefinition(), 
             aggregator_data=CRUD_AggregatorData(main_table_key=action_log_table.key, aggregator=ActionLogAggregator(), attribute='invalid_files'))