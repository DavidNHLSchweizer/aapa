from data.classes.undo_logs import UndoLog
from storage.general.CRUDs import CRUDQueries

class UndoLogQueries(CRUDQueries):
    def last_undo_log(self)->UndoLog:
        if last_id:=self.find_max_value(attribute='id', 
                                     where_attributes='can_undo',
                                     where_values = True):
            return self.crud.read(last_id)
        return None
