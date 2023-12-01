from data.classes.action_logs import ActionLog
from data.storage.aapa_storage import AAPAStorage, StorageExtension


class ActionLogStorageExtension(StorageExtension):
    def __init__(self, storage: AAPAStorage):
        super().__init__(storage, 'action_logs')
    def last_action_log(self)->ActionLog:
        if last_id:=self.storage.find_max_value('action_logs', attribute='id', 
                                     where_attributes='can_undo',
                                     where_values = True):
            return self.storage.read('action_logs', last_id)
        return None
