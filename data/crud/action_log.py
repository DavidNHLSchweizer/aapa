from dataclasses import dataclass
from typing import Iterable
from data.aapa_database import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog
from data.crud.crud_base import AAPAClass, CRUDbase
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug
from general.timeutil import TSC

class CRUD_action_log(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, class_type=ActionLog, table=ActionLogTableDefinition(), autoID=True)
        self._db_map['date']['db2obj'] = TSC.str_to_timestamp
        self._db_map['date']['obj2db'] = TSC.timestamp_to_str
        self._db_map['can_undo']['db2obj'] = bool
        self._db_map['can_undo']['obj2db'] = int
        self._db_map['action']['db2obj'] = ActionLog.Action

@dataclass
class ActionLogRelationRec:
    log_id: int 
    rel_id: int
ActionLogRelationRecs = list[ActionLogRelationRec]

class CRUD_action_log_relations(CRUDbase):
    def __init__(self, database: Database, relation_table: TableDefinition):
        super().__init__(database, class_type=None, table=relation_table) #TBD
    def _get_relation_column_name(self)->str:
        log_debug(f'GRC: {self.table.keys[1]}')
        return self.table.keys[1]
    def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
        return None #implement in descendants
    def get_relation_records(self, action_log: ActionLog)->ActionLogRelationRecs:
        return [ActionLogRelationRec(action_log.id, object.id) 
                for object in sorted(self._get_objects(action_log), key=lambda o: o.id)]
                #gesorteerd om dat het anders in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    def create(self, action_log: ActionLog):
        for record in self.get_relation_records(action_log):
            self.database.create_record(self.table, columns=self._get_all_columns(), 
                                        values=[record.log_id, record.rel_id])   
    def read(self, action_log_id: int)->ActionLogRelationRecs: 
        result = []
        if rows:=super().read(action_log_id, multiple=True):
            for row in rows:
                result.append(ActionLogRelationRec(log_id=action_log_id, rel_id=row[self._get_relation_column_name()]))
        return result
    def update(self, action_log: ActionLog):
        def is_changed()->bool:
            new_records = self.get_relation_records(action_log)
            current_records= self.read(action_log.id)
            if len(new_records) != len(current_records):
                return True
            else:
                for new, current in zip(new_records, current_records):
                    if new != current:
                        return True
            return False
        if is_changed():
            self._update(action_log)
    def _update(self, action_log: ActionLog):        
        self.delete(action_log.id)    
        self.create(action_log)
    def delete_relation(self, rel_id: int):
        self.database._execute_sql_command(f'delete from {self.table.name} where {self._get_relation_column_name()}=?', [rel_id])        

class CRUD_action_log_aanvragen(CRUD_action_log_relations):
    def __init__(self, database: Database):
        super().__init__(database, ActionLogAanvragenTableDefinition())
    def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
        return action_log.aanvragen

class CRUD_action_log_invalid_files(CRUD_action_log_relations):
    def __init__(self, database: Database):
        super().__init__(database, ActionLogFilesTableDefinition())
    def _get_objects(self, action_log: ActionLog)->Iterable[AAPAClass]:
        return action_log.invalid_files