from data.classes.action_logs import ActionLog
from data.storage.CRUDs import CRUDQueries

class ActionLogQueries(CRUDQueries):
    def last_action_log(self)->ActionLog:
        if last_id:=self.find_max_value(attribute='id', 
                                     where_attributes='can_undo',
                                     where_values = True):
            return self.crud.read(last_id)
        return None
