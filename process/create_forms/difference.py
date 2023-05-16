import difflib
import html
from pathlib import Path
from data.classes import AanvraagInfo, FileType
from general.fileutil import summary_string
from general.log import logPrint
from process.aanvraag_processor import AanvraagProcessor

from process.importing.import_data import PDFaanvraagReader

class DifferenceGenerator:
    def __init__(self, version1, version2: str):
        self.table_lines1 = PDFaanvraagReader(version1).all_lines()
        self.table_lines2 = PDFaanvraagReader(version2).all_lines()
        self.version1 = version1
        self.version2 = version2
        self.html_differ = difflib.HtmlDiff()
    def generate_html(self, html_file: str, context=False):
        def diff_column_header(msg, filename):
            return html.escape(f'({msg}) {Path(filename).name}')
        with open(html_file, "w", encoding='utf8') as file:
            file.write(self.html_differ.make_file(self.table_lines1, self.table_lines2, 
                            fromdesc=diff_column_header('oud', self.version1), 
                            todesc=diff_column_header('nieuw', self.version2), 
                            context=context))

class DifferenceProcessor(AanvraagProcessor):
    def find_previous_version(self, aanvraag: AanvraagInfo)->AanvraagInfo:
        aanvragen = self.storage.find_aanvragen(aanvraag.student, aanvraag.bedrijf)
        if aanvragen:
            aanvragen.sort(key=lambda a: a.timestamp, reverse=True)
        if len(aanvragen)>1:
            return aanvragen[1]
        else:
            return None
    def get_difference_filename(self, output_directory, student):
        return Path(output_directory).joinpath(f'Veranderingen in aanvraag {student.student_name}.html')           
    def create_difference(self, previous_aanvraag: AanvraagInfo, aanvraag: AanvraagInfo, output_directory, preview=False)->str:
            version1 = previous_aanvraag.aanvraag_source_file_name()
            version2 = aanvraag.aanvraag_source_file_name()
            difference_filename= self.get_difference_filename(output_directory, aanvraag.student)            
            if not preview:
                DifferenceGenerator(version1, version2).generate_html(difference_filename)
            aangemaakt = 'aan te maken' if preview else 'aangemaakt'
            vergeleken = 'te vergelijken' if preview else 'vergeleken'
            print(f'\tVerschil-bestand "{summary_string(difference_filename)}" {aangemaakt}.\n\tNieuwste versie "{summary_string(version2)}" {vergeleken} met\n\tvorige versie "{summary_string(version1)}"')
            aanvraag.files.set_filename(FileType.DIFFERENCE_HTML, difference_filename)        
    def process_aanvraag(self, aanvraag: AanvraagInfo, output_directory, preview = False):
        if (previous_aanvraag := self.find_previous_version(aanvraag)) is not None:
            self.create_difference(previous_aanvraag, aanvraag, output_directory, preview=preview)
        else:
            logPrint(f'\tGeen vorige versie van aanvraag {aanvraag} bekend.')
    def process_student(self, studnr, output_directory, preview = False):
        if (student := self.storage.read_student(studnr)) is None:
            logPrint(f'Student {studnr} niet bekend.')
            return
        if (aanvragen := self.storage.find_aanvragen_for_student(student)) is None:
            logPrint(f'Geen aanvragen gevonden voor student {student}.')
            return
        if len(aanvragen) <= 1:
            logPrint(f'Geen oudere versies gevonden voor student {student}.')
            return
        aanvragen.sort(key=lambda a: a.timestamp, reverse=True)
        self.create_difference(aanvragen[1], aanvragen[0], output_directory=output_directory, preview=preview)

# def create_difference_file_for_aanvraag(s(storage: AAPStorage, template_doc, output_directory, filter_func = None, preview=False)->int:aanvraag: AanvraagInfo)
