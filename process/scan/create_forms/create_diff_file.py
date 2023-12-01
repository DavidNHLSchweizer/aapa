from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.storage.aapa_storage import AAPAStorage
from general.fileutil import file_exists, safe_file_name, summary_string
from general.log import log_debug, log_print
from general.preview import pva
from process.general.difference import DifferenceGenerator
from process.general.aanvraag_processor import AanvraagProcessor

class DifferenceProcessor(AanvraagProcessor):
    def __init__(self, storage: AAPAStorage, output_directory: str):
        self.output_directory = Path(output_directory)
        self.storage = storage
        super().__init__(entry_states={Aanvraag.Status.IMPORTED_PDF, Aanvraag.Status.NEEDS_GRADING},
                         description='Aanmaken verschilbestand')
    def find_previous_aanvraag(self, aanvraag: Aanvraag)->Aanvraag:
        if aanvraag.versie == 1:
            return None
        self.storage.ensure_key('studenten', aanvraag.student)
        if result := self.storage.find_values('aanvragen', attributes=['versie', 'student'], values=[aanvraag.versie-1, aanvraag.student.id]):
            return result[0]
        return None
    def get_difference_filename(self, output_directory:str, student_name: str)->str:
        return Path(output_directory).joinpath(f'Veranderingen in aanvraag {safe_file_name(student_name)}).html')
    def create_difference(self, previous_aanvraag: Aanvraag, aanvraag: Aanvraag, output_directory='', preview=False)->str:
            version1 = previous_aanvraag.aanvraag_source_file_path()
            version2 = aanvraag.aanvraag_source_file_path()
            difference_filename= self.get_difference_filename(output_directory, aanvraag.student.full_name)            
            if not preview:
                DifferenceGenerator(version1, version2).generate_html(difference_filename)                
            aanvraag.register_file(difference_filename, File.Type.DIFFERENCE_HTML)
            log_print(f'\tVerschil-bestand "{summary_string(difference_filename)}" {pva(preview, "aan te maken", "aangemaakt")}.')
            log_print(f'\t\tNieuwste versie "{aanvraag.summary()} ({aanvraag.kans})" {pva(preview, "te vergelijken", "vergeleken")} met\n\t\tvorige versie "{previous_aanvraag.summary()} ({previous_aanvraag.kans})".')
    def process(self, aanvraag: Aanvraag, preview = False, output_directory='.')->bool:
        if (previous_aanvraag := self.find_previous_aanvraag(aanvraag)):
            if not file_exists(self.get_difference_filename(self.output_directory, aanvraag.student.full_name)):
                log_print(f'\tVerschilbestand met vorige versie aanmaken')
                self.create_difference(previous_aanvraag, aanvraag, output_directory=output_directory, preview=preview)
                return True
        else:
            if aanvraag.status in {Aanvraag.Status.IMPORTED_PDF}:
                log_print(f'\tGeen vorige versie van aanvraag {aanvraag} bekend.')
                return True
        return False