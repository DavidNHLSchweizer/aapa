from data.classes.action_logs import ActionLog
from data.storage.CRUDs import CRUD, CRUDQueries

class ActionLogQueries(CRUDQueries):
    def __init__(self, crud: CRUD):
        super().__init__(crud)
    def last_action_log(self)->ActionLog:
        if last_id:=self.find_max_value('action_logs', attribute='id', 
                                     where_attributes='can_undo',
                                     where_values = True):
            return self.read('action_logs', last_id)
        return None
