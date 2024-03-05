import re
from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.const import MijlpaalType
from data.classes.files import File
from main.log import log_error
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from storage.general.storage_const import StorageException
from storage.queries.mijlpaal_directories import MijlpaalDirectoriesQueries
from storage.queries.student_directories import StudentDirectoriesQueries
from tests.random_data import RandomData

class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        self.stud_dir_queries:StudentDirectoriesQueries=self.storage.queries('student_directories')
        self.mp_dir_queries: MijlpaalDirectoriesQueries = self.storage.queries('mijlpaal_directories')
        self.week_pattern = re.compile(r'.*week [\d]+.*',re.IGNORECASE)

        return True

    def _aanvraag_file_in_week_directory(self, aanvraag: Aanvraag, file: File)->bool:
        return file.filetype in {File.Type.AANVRAAG_PDF,File.Type.GRADE_FORM_PDF} and \
            self.week_pattern.match(file.filename) is not None
    def _find_mp_dir_from_aanvraag(self, aanvraag: Aanvraag)->MijlpaalDirectory:
        if not (mp_dirs := self.stud_dir_queries.find_student_mijlpaal_dir(aanvraag.student,MijlpaalType.AANVRAAG)):
            return None
        return mp_dirs[-1]        
    def find_mp_dir_aanvraag(self, aanvraag: Aanvraag)->MijlpaalDirectory:
        directory = aanvraag.get_directory()              
        if directory and not self.week_pattern.match(directory):
            return self.mp_dir_queries.find_mijlpaal_directory(directory)
        return self._find_mp_dir_from_aanvraag(aanvraag)
    def dump_aanvraag(self, aanvraag: Aanvraag):
        print('..............')
        print(f'Aanvraag: {aanvraag.summary()}; Aanvraag id: {aanvraag.id}\n\tAanvraag dir: {File.display_file(aanvraag.get_directory())}')
        print(f'\tFiles:\n{"\n\t\t".join([f'{file.id}: {File.display_file(file.filename)}' for file in aanvraag.files_list])}')
        print('..............')
    def dump_mp_dir(self, mp_dir: MijlpaalDirectory):
        print('----------')
        print(f'Mijlpaal Directory: {mp_dir.summary()}')
        print(f'\tFiles:\n{"\n\t\t".join([f'{file.id}: {File.display_file(file.filename)}' for file in mp_dir.get_files()])}')
        print('----------')
    def _process_aanvraag(self, aanvraag: Aanvraag):
        try:
            mp_dir = self.find_mp_dir_aanvraag(aanvraag)
            if not mp_dir:
                print('====================')
                log_error(f'Mijlpaal Directory not found for aanvraag {aanvraag}')
                print(f'Mijlpaal Directory not found for aanvraag {aanvraag}' )
                self.dump_aanvraag(aanvraag)
                print('====================')
            else:
                mp_dir.mijlpalen.add(aanvraag)
                self.storage.update('mijlpaal_directories', mp_dir)
        except Exception as E:
            print('====================')
            print(f'Exception: {E}')
            if aanvraag:
                self.dump_aanvraag(aanvraag)
            if mp_dir:
                self.dump_mp_dir(mp_dir)
            print('====================')
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        # for aanvraag in sorted(self.storage.queries('aanvragen').find_all(),key=lambda a:a.student.id):
        if (aanvraag := self.storage.read('aanvragen', 232)):
            self._process_aanvraag(aanvraag)                               
        # self.database.commit()
        return True
    