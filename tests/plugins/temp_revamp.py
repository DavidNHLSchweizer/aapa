from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.const import MijlpaalType
from data.classes.files import File
from main.log import log_error
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from storage.general.storage_const import StorageException
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

    def dump_aanvraag(self, aanvraag: Aanvraag):
        print(f'Aanvraag: {aanvraag.summary()}; Aanvraag id: {aanvraag.id}\n\tAanvraag dir: {File.display_file(aanvraag.get_directory())}')
        print(f'\tFiles:\n{"\n\t\t".join([f'{file.id}: {File.display_file(file.filename)}' for file in aanvraag.files_list])}')
    def dump_mp_dir(self, mp_dir: MijlpaalDirectory):
        print(f'Mijlpaal Directory: {mp_dir.summary()}')
        print(f'\tFiles:\n{"\n\t\t".join([f'{file.id}: {File.display_file(file.filename)}' for file in mp_dir.files_list])}')
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        for n, aanvraag in enumerate(sorted(self.storage.queries('aanvragen').find_all(),key=lambda a:a.student.id)):
            try:
                # print(f'{n+1}: {aanvraag.summary()}')
                # if n <= 60: continue
                mp_dir = self.find_mp_dir_aanvraag(aanvraag)
                if not mp_dir:
                    # log_error(f'Mijlpaal Directory not found for aanvraag {aanvraag}')
                    print(f'Mijlpaal Directory not found for aanvraag {aanvraag}' )
                    self.dump_aanvraag(aanvraag)
                    continue
                else:
                    mp_dir.mijlpalen.add(aanvraag)
                    self.storage.update('mijlpaal_directories', mp_dir)                
            except Exception as E:
                print(f'Exception: {E}')
                if aanvraag:
                    self.dump_aanvraag(aanvraag)
                if mp_dir:
                    self.dump_mp_dir(mp_dir)
            # if n >= 60:
            #     break
        # self.database.commit()
        return True
    