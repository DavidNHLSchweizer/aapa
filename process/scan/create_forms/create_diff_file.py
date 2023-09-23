from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.fileutil import file_exists, summary_string
from general.log import log_print
from general.preview import pva
from process.general.difference import DifferenceGenerator
from process.general.aanvraag_processor import AanvraagProcessor

class DifferenceProcessor(AanvraagProcessor):
    def __init__(self, all_aanvragen: list[Aanvraag], output_directory: str):
        self.output_directory = Path(output_directory)
        self.all_aanvragen = all_aanvragen
    def find_previous_aanvraag(self, aanvraag: Aanvraag)->Aanvraag:
        relevante_aanvragen = list(filter(lambda a: a.id < aanvraag.id and \
                                        a.student.stud_nr==aanvraag.student.stud_nr and \
                                        a.bedrijf.id == aanvraag.bedrijf.id, self.all_aanvragen))
        if len(relevante_aanvragen)>=1:            
            return sorted(relevante_aanvragen, key=lambda a: a.aanvraag_nr, reverse=True)[0]
        else:
            return None
    def get_difference_filename(self, output_directory:str, student_name: str)->str:
        return Path(output_directory).joinpath(f'Veranderingen in aanvraag {student_name}.html')
    def create_difference(self, previous_aanvraag: Aanvraag, aanvraag: Aanvraag, output_directory='', preview=False)->str:
            version1 = previous_aanvraag.aanvraag_source_file_name()
            version2 = aanvraag.aanvraag_source_file_name()
            difference_filename= self.get_difference_filename(output_directory, aanvraag.student.full_name)            
            if not preview:
                DifferenceGenerator(version1, version2).generate_html(difference_filename)                
            aanvraag.register_file(difference_filename, File.Type.DIFFERENCE_HTML)
            log_print(f'\tVerschil-bestand "{summary_string(difference_filename)}" {pva(preview, "aan te maken", "aangemaakt")}.')
            log_print(f'\t\tNieuwste versie "{summary_string(version2, maxlen=80)}" {pva(preview, "te vergelijken", "vergeleken")} met\n\t\tvorige versie "{summary_string(version1, maxlen=80)}".')
    def must_process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:      
        return aanvraag.status in {Aanvraag.Status.INITIAL, Aanvraag.Status.NEEDS_GRADING} 
    def process(self, aanvraag: Aanvraag, preview = False, output_directory='.')->bool:
        if (previous_aanvraag := self.find_previous_aanvraag(aanvraag)):
            if not file_exists(self.get_difference_filename(self.output_directory, aanvraag.student.full_name)):
                log_print(f'\tVerschilbestand met vorige versie {pva(preview, "aan te maken", "aangemaakt")}')
                self.create_difference(previous_aanvraag, aanvraag, output_directory=output_directory, preview=preview)
                return True
        else:
            if aanvraag.status in {Aanvraag.Status.INITIAL}:
                log_print(f'\tGeen vorige versie van aanvraag {aanvraag} bekend.')
                return True
        return False