from pathlib import Path
from data.classes.base_dirs import BaseDir
from data.general.roots import Roots
from storage.general.CRUDs import CRUDQueries
from storage.general.storage_const import StorageException
from general.log import log_debug

class BaseDirQueries(CRUDQueries):
    def is_basedir(self, directory: str|Path)->bool:    
        directory = str(directory)
        if not directory:
            return False        
        encoded = Roots.encode_path(directory)
        log_debug(f'BDQ: {directory}->{encoded}')
        result = self.find_values(attributes='directory', values=encoded)
        log_debug(f'is_basedir: encoded: {encoded} dus {result != []}')
        return result != []
    def find_basedir(self, directory: str|Path, start_at_parent = True)->BaseDir:
        if directory == '' or directory==(parent:=str(Path(directory).parent)):
            return None        
        candidate_basedir = parent if start_at_parent else directory
        encoded = Roots.encode_path(candidate_basedir)
        log_debug(f'encoded: {encoded}')
        if stored:=self.find_values(attributes='directory', values=candidate_basedir):
            if len(stored) > 1:
                raise StorageException(f'More than one basedir with same name in database:\n{[str(basedir) for basedir in stored]}')
            return stored[0]
        return self.find_basedir(candidate_basedir)
    def last_base_dir(self)->BaseDir:
        return self.crud.read(self.find_max_value('id'))
