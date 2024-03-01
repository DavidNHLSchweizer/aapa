from data.classes.undo_logs import UndoLog
from main.options import AAPAProcessingOptions
from storage.general.CRUDs import CRUDQueries

class UndoLogsQueries(CRUDQueries):
    def last_undo_log(self, processing_mode: AAPAProcessingOptions.PROCESSINGMODE)->UndoLog:
        if last_id:=self.find_max_value(attribute='id',
                                     where_attributes=['can_undo', 'processing_mode'],
                                     where_values = [True, processing_mode]):
            return self.crud.read(last_id)
        return None
