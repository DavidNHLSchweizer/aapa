from data.classes.mijlpaal_directories import MijlpaalDirectory
from storage.general.CRUDs import CRUDQueries

class MijlpaalDirectoriesQueries(CRUDQueries):
    def find_mijlpaal_directory(self, directory: str)->MijlpaalDirectory:
        if (values := self.find_values('directory', directory)):
            return values[0]
        return None
        