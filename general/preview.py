from data.storage.aapa_storage import AAPAStorage
from general.log import console_info
class Preview:
    # preview context manager, may be nested
    level = 0
    def __init__(self, preview:bool, storage: AAPAStorage, msg):
        self.preview=preview
        self.storage = storage
        self.msg=msg
    def __enter__(self):
        if self.preview and Preview.level == 0:
            self.storage.database.disable_commit()
            console_info('*** PREVIEW ONLY ***')
        Preview.level += 1
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        Preview.level -=1
        if self.preview and Preview.level == 0:
            self.storage.database.rollback()
            self.storage.database.enable_commit()
            console_info('*** end  PREVIEW ***')

    
def pva(preview: bool, action_preview: str, action_actual: str)->str: 
    return action_preview if preview else action_actual