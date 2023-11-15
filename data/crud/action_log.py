from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog
from data.crud.aanvragen import CRUD_aanvragen
from data.crud.crud_base import AAPAClass, CRUDbase, CRUDbaseDetails
from data.crud.crud_factory import registerCRUD
from data.crud.files import CRUD_files
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug
from general.timeutil import TSC

class CRUD_action_log_aanvragen(CRUDbaseDetails):
    # def __init__(self, database: Database):
    #     super().__init__(CRUD_action_log(database), ActionLogAanvragenTableDefinition())
    def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
        return action_log.aanvragen

class CRUD_action_log_invalid_files(CRUDbaseDetails):
    # def __init__(self, database: Database):
    #     super().__init__(CRUD_action_log(database), ActionLogFilesTableDefinition())
    def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
        return action_log.invalid_files


class CRUD_action_log(CRUDbase):
    def _after_init_(self):
        self._db_map['date']['db2obj'] = TSC.str_to_timestamp
        self._db_map['date']['obj2db'] = TSC.timestamp_to_str
        self._db_map['can_undo']['db2obj'] = bool
        self._db_map['can_undo']['obj2db'] = int
        self._db_map['action']['db2obj'] = ActionLog.Action  
    def add_details(self, action_log: ActionLog, crud_details: CRUDbaseDetails, crud_table: CRUDbase):
        for record in crud_details.read(action_log.id):
            action_log.add(crud_table.read(record.detail_id))
    def _post_process_read(self, action_log: ActionLog)->ActionLog:
        DETAILS = [
                { 'crud_details':CRUD_action_log_aanvragen, 'crud_table': CRUD_aanvragen},
                { 'crud_details':CRUD_action_log_invalid_files, 'crud_table': CRUD_files}
                ]
        #adds detail records as needed
        for record in DETAILS:
            self.add_details(action_log, record['crud_details'](self.database), record['crud_table'](self.database))            
            return action_log

registerCRUD(CRUD_action_log, class_type=ActionLog, table=ActionLogTableDefinition(), autoID=True)