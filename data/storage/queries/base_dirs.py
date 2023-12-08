from pathlib import Path
from data.classes.base_dirs import BaseDir
from data.roots import encode_path
from data.storage.CRUDs import CRUDQueries
from data.storage.general.storage_const import StorageException
from general.log import log_debug

class BaseDirQueries(CRUDQueries):
    def find_basedir(self, directory: str|Path)->BaseDir:
        if directory == '':
            return None        
        candidate_basedir = str(Path(directory).parent)
        encoded = encode_path(candidate_basedir)
        log_debug(f'encoded: {encoded}')
        if stored:=self.find_values(attributes='directory', values=candidate_basedir):
            if len(stored) > 1:
                raise StorageException(f'More than one basedir with same name in database:\n{[str(basedir) for basedir in stored]}')
            return stored[0]
        return self.find_basedir(candidate_basedir)
