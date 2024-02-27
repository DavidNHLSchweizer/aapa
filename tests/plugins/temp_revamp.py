from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.const import MijlpaalType
from data.classes.files import File
from main.log import log_error
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from storage.queries.mijlpaal_directories import MijlpaalDirectoriesQueries
from tests.random_data import RandomData

class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True

    def find_mp_dir_aanvraag(self, aanvraag: Aanvraag)->MijlpaalDirectory:
        mp_dir_queries: MijlpaalDirectoriesQueries = self.storage.queries('mijlpaal_directories')
        return mp_dir_queries.find_mijlpaal_directory(aanvraag.get_directory())

    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        for n, aanvraag in enumerate(self.storage.queries('aanvragen').find_all()):
            print(f'{n+1}: {aanvraag.summary()}')
            if n <= 52: continue
            mp_dir = self.find_mp_dir_aanvraag(aanvraag)
            if not mp_dir:
                log_error(f'Mijlpaal Directory not found for aanvraag {aanvraag}')
                continue
            else:
                mp_dir.mijlpalen.add(aanvraag)
                self.storage.update('mijlpaal_directories', mp_dir)
            # if n >= 52:
            #     break
        self.database.commit()
        return True
    