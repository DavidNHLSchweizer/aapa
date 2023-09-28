from dataclasses import dataclass
from data.AAPdatabase import ActionLogAanvragenTableDefinition, ActionLogTableDefinition
from data.classes.action_log  import ActionLog
from data.crud.crud_base import CRUDbase
from database.database import Database
from general.keys import get_next_key
from general.timeutil import TSC

class CRUD_action_log(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ActionLogTableDefinition(), ActionLog)
        self._db_map['date']['db2obj'] = TSC.str_to_timestamp
        self._db_map['date']['obj2db'] = TSC.timestamp_to_str
        self._db_map['can_undo']['db2obj'] = bool
        self._db_map['can_undo']['obj2db'] = int
        self._db_map['action']['db2obj'] = ActionLog.Action
    def create(self, action_log: ActionLog):
        action_log.id = get_next_key(ActionLogTableDefinition.KEY_FOR_ID)
        super().create(action_log)                          

@dataclass
class ActionLogAanvraagRec:
    log_id: int 
    aanvraag_id: int
ActionLogAanvraagRecs = list[ActionLogAanvraagRec]

class CRUD_action_log_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ActionLogAanvragenTableDefinition(), None) #TBD
    def get_aanvraag_records(self, action_log: ActionLog)->ActionLogAanvraagRecs:
        return [ActionLogAanvraagRec(action_log.id, aanvraag.id) 
                for aanvraag in sorted(action_log.aanvragen, key=lambda a: a.id)]
                #gesorteerd om dat het anders in omgekeerde volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    def create(self, action_log: ActionLog):
        for record in self.get_aanvraag_records(action_log):
            self.database.create_record(self.table, columns=self._get_all_columns(), values=[record.log_id, record.aanvraag_id])   
    def read(self, action_log_id: int)->ActionLogAanvraagRecs: 
        result = []
        for row in super().read(action_log_id, multiple=True):
            result.append(ActionLogAanvraagRec(log_id=action_log_id, aanvraag_id=row['aanvraag_id']))
        return result
    def update(self, action_log: ActionLog):
        def is_changed()->bool:
            new_records = self.get_aanvraag_records(action_log)
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
    def delete_aanvraag(self, aanvraag_id: int):
        self.database._execute_sql_command(f'delete from {self.table.table_name} where aanvraag_id=?', [aanvraag_id])        
