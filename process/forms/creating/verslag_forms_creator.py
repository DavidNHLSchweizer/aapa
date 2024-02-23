from pathlib import Path
from data.classes.verslagen import Verslag
from data.classes.files import File
from general.singular_or_plural import sop
from main.log import log_error, log_print
from process.forms.creating.verslag_version_forms_creator import VerslagVersionFormsCreator
from process.general.preview import pva
from process.general.student_dir_builder import StudentDirectoryBuilder
from process.general.verslag_processor import VerslagProcessor
from storage.aapa_storage import AAPAStorage
from storage.queries.student_directories import StudentDirectoryQueries

class FormsException(Exception): pass

class VerslagFormsCreator(VerslagProcessor):
    def __init__(self, storage: AAPAStorage):
        super().__init__(entry_states={Verslag.Status.NEW, Verslag.Status.NEW_MULTIPLE}, 
                         exit_state=Verslag.Status.NEEDS_GRADING,
                         description='Aanmaken beoordelingsformulieren')
        self.storage=storage
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        self.builder = StudentDirectoryBuilder(self.storage)
    def process(self, verslag: Verslag, preview=False, **kwdargs)->bool:
        if not verslag:
            return False
        stud_dir = self.student_dir_queries.find_student_dir(verslag.student) 
        if not stud_dir:
            raise FormsException(f'Kan formulieren voor {verslag.summary()} niet aanmaken\n\t(kan student directory niet bepalen).')
        version = stud_dir.base_dir.forms_version      
        directory = Path(self.builder.get_mijlpaal_directory_name(stud_dir, verslag.datum, verslag.mijlpaal_type))
        if not directory:
            raise FormsException(f'Kan juiste directory voor formulieren {verslag.summary()} niet bepalen.')        
        creator = VerslagVersionFormsCreator(self.storage, version)
        created = creator.create_forms(verslag, directory, preview=preview)
        aangemaakt = pva(preview,'aanmaken', 'aangemaakt')
        if not created:
            log_error(f'Geen formulieren {aangemaakt}')
            return False
        filename,_ = created[0]
        log_print(f'{sop(len(created), 'formulier', 'formulieren')} {aangemaakt} in {File.display_file(Path(filename).parent)}')
        for filename,filetype in created:
            log_print(f'\t{File.display_file(Path(filename).name)} [{filetype}].')
            verslag.register_file(filename, filetype, verslag.mijlpaal_type)
        return True