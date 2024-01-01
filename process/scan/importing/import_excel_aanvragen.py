from enum import IntEnum
from pathlib import Path
from mailmerge import MailMerge
from typing import Any, Iterable, Tuple
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student

from data.classes.undo_logs import UndoLog
from data.storage.aapa_storage import AAPAStorage
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.storage.queries.aanvragen import AanvraagQueries
from debug.debug import MAJOR_DEBUG_DIVIDER
from general.log import log_debug, log_error, log_print, log_warning, log_info
from general.preview import pva
from general.singular_or_plural import sop
from general.config import config
from general.fileutil import created_directory, last_parts_file, path_with_suffix, safe_file_name, test_directory_exists
from general.strutil import replace_all
from general.timeutil import TSC
from process.general.aanvraag_pipeline import AanvraagCreatorPipeline
from process.general.aanvraag_processor import AanvraagCreator
from process.general.student_dir_builder import StudentDirectoryBuilder
from process.general.word_processor import Word2PdfConvertor
from process.scan.create_forms.create_form import MailMergeException
from process.scan.importing.aanvraag_importer import AanvraagImporter
from process.scan.importing.excel_reader import ExcelReader

def init_config():
    config.init('import', 'xls_template', r'.\templates\2. Aanvraag goedkeuring afstudeeropdracht nieuwe vorm MAILMERGE.docx')
init_config()


class AanvragenFromExcelImporter(AanvraagImporter):
    class ColNr(IntEnum):
        ID          = 0
        BEGINTIJD   = 1
        VOLTOOIEN   = 2
        EMAIL       = 3
        NAAM        = 4
        WIJZIGING   = 5
        STUDNR      = 6
        TELNR       = 7
        VT_DT       = 8
        BEDRIJF     = 9
        BEDR_ADRES  = 10
        BEDR_WWW    = 11
        BEDR_BEGL   = 12
        BEDR_BEGL_FIE  = 13
        BEDR_BEGL_EML  = 14
        BEDR_BEGL_TEL  = 15
        BRON        = 16
        START       = 17
        KERNTAKEN   = 18
        BELANG      = 19
        BEGELEIDING = 20
        TITEL       = 21
        AANLEIDING  = 22
        OMSCHRIJVING= 23
        BER_PRODUCTEN = 24
        SW_PRODUCTEN  = 25
        ONDZ_VERMOGEN = 26
        ANALYSE     = 27 
        ONTWERP     = 28
        TEST        = 29
        KWALITEIT   = 30
        TECHNIEK    = 31
    ENQUETE_COLUMNS= \
    { ColNr.ID: 'ID', 
      ColNr.BEGINTIJD: 'Begintijd', 
      ColNr.VOLTOOIEN: 'Tijd van voltooien', 
      ColNr.EMAIL: 'E-mail', 
      ColNr.NAAM: 'Naam',
      ColNr.WIJZIGING: 'Tijd van laatste wijziging', 
      ColNr.STUDNR: 'Wat is je studentnummer',
      ColNr.TELNR: 'Wat is je telefoonnummer', 
      ColNr.VT_DT: 'Hoe ga je afstuderen?',
      ColNr.BEDRIJF: 'Bij welk bedrijf ga je afstuderen?',
      ColNr.BEDR_ADRES: 'Wat is het adres van het afstudeerbedrijf?',
      ColNr.BEDR_WWW:  'Wat is de website van het bedrijf?',
      ColNr.BEDR_BEGL: 'Wat is de naam van je bedrijfsbegeleider?',
      ColNr.BEDR_BEGL_FIE: 'Wat is de functie van deze bedrijfsbegeleider?',
      ColNr.BEDR_BEGL_EML: 'Wat is het e-mail adres van deze bedrijfsbegeleider',
      ColNr.BEDR_BEGL_TEL: 'Wat is het telefoonnummer van deze bedrijfsbegeleider',
      ColNr.BRON: 'Hoe heb je deze opdracht gevonden?',
      ColNr.START: 'Wanneer wil je starten met je afstudeeropdracht?',
      ColNr.KERNTAKEN: 'Kerntaken van het bedrijf',
      ColNr.BELANG: 'Wat is het belang voor de opdrachtgever bij deze opdracht?',
      ColNr.BEGELEIDING: 'Begeleiding',
      ColNr.TITEL: '(Voorlopige, maar beschrijvende) Titel van de afstudeeropdracht',
      ColNr.AANLEIDING: 'Wat is de aanleiding voor de opdracht? \n',
      ColNr.OMSCHRIJVING: 'Korte omschrijving van de opdracht\n',
      ColNr.BER_PRODUCTEN:  'Wat zijn de op te leveren beroepsproducten uit jouw project?\n ',
      ColNr.SW_PRODUCTEN: 'Wat zijn de op te leveren softwareproduct(en) uit jouw project? \n',
      ColNr.ONDZ_VERMOGEN: 'Onderzoekend vermogen: welke ruimte is er in de opdracht om zaken te onderzoeken? \n ',
      ColNr.ANALYSE: 'Analysefase: Hoe kom je aan de (functionele/non functionele) requirements? \n',
      ColNr.ONTWERP: 'Ontwerpfase: Hoe ga je ontwerpen (werkwijze, methode) en wat ontwerp je (voorlopig)?',
      ColNr.TEST: 'Testfase: hoe kun je de kwaliteit van je softwareproduct aantonen? \n',
      ColNr.KWALITEIT: 'Kwaliteitsbewaking: welke processen ga je inzetten om grip te houden op je kwaliteit en voortgang?\n ',
      ColNr.TECHNIEK: 'Welke technieken/frameworks ga je inzetten en welke hiervan heb je nog geen ervaring mee. \n',
    }
    def __init__(self, output_directory: str, storage: AAPAStorage):
        super().__init__(f'import from excel-file', multiple=True)
        self.template = config.get('import', 'xls_template')
        self.storage = storage
        self.output_directory = output_directory
        with MailMerge(self.template) as document:
            self.merge_fields = document.get_merge_fields()   
                 
    def find_merge_field_vraag(self, merge_field: str)->str:
        def _standardize_vraag(vraag: str)->str:
            return replace_all(replace_all(vraag, ':/(),-', ''), ' ?\n', '_').replace('___', '__')
        for vraag in self.ENQUETE_COLUMNS.values():
            vraag2 = _standardize_vraag(vraag)
            if vraag2.find(merge_field)==0:
                return vraag
        return 'not found'
    def __get_value(self, values: dict[str, Any], colnr: ColNr)->str:
        return str(values.get(self.ENQUETE_COLUMNS.get(colnr, colnr.name)))
    def _get_student(self, values:dict[str, Any])->Student:
        return Student(full_name=self.__get_value(values, self.ColNr.NAAM),
                          stud_nr=self.__get_value(values, self.ColNr.STUDNR),
                          email=self.__get_value(values, self.ColNr.EMAIL))
    def _get_bedrijf(self, values: dict[str,Any])->Bedrijf:
        return Bedrijf(self.__get_value(values, self.ColNr.BEDRIJF))
    def _get_aanvraag(self, values: dict[str, Any])->Aanvraag:
        return Aanvraag(self._get_student(values), self._get_bedrijf(values), 
                        datum = TSC.sortable_str_to_timestamp(self.__get_value(values, self.ColNr.VOLTOOIEN)),
                        titel = self.__get_value(values, self.ColNr.TITEL),
                        )
    def get_filename(self, values: dict[str, Any])->str:
        student = self._get_student(values)
        student_directory = Path(StudentDirectoryBuilder.get_student_dir_name(self.storage,student,self.output_directory))
        datum = self.__get_value(values, self.ColNr.VOLTOOIEN)
        bedrijf = self._get_bedrijf(values)
        return str(student_directory.joinpath(safe_file_name(f'2. Aanvraag Afstuderen {datum}-{student.full_name}-{bedrijf.name}.docx')))   
    def create_file(self, values: dict[str, Any], preview=False)->str:
        filename = self.get_filename(values)
        directory = Path(filename).parent
        if not test_directory_exists(str(directory)):
            if preview:
                log_info(f'Directory {directory} aanmaken.')
            else:
                if created_directory(str(directory)):
                    log_info(f'Directory {directory} aangemaakt.')
        if not preview:
            merge_dict = {field: str(values.get(self.find_merge_field_vraag(field), '?')) 
                          for field in self.merge_fields}
            with MailMergeException(self.template) as document:
                document.merge(**merge_dict)
                document.write(filename)
        return filename
    def create_pdf_file(self, docx_filename: str, preview=False)->str:
        pdf_filename = str(path_with_suffix(docx_filename, '.pdf'))
        if not preview:
            Word2PdfConvertor().convert(docx_filename, pdf_filename)
            Path(docx_filename).unlink()
        return pdf_filename
    def process_values(self, values: dict[str, Any], preview=False)->Tuple[Aanvraag, str]:
        pdf_filename = self.create_pdf_file(self.create_file(values, preview), preview)
        log_print(f'Aanvraagbestand {last_parts_file(pdf_filename)} {pva(preview, "aanmaken", "aangemaakt")}.')
        return (self._get_aanvraag(values), pdf_filename)
    def read_aanvragen(self, filename: str, preview: bool)->Iterable[Tuple[Aanvraag, str]]:
        reader = ExcelReader(filename, self.ENQUETE_COLUMNS.values())
        if reader.error:
            log_error(f'{reader.error}')
            return None
        for values in reader.read():
            (aanvraag,aanvraag_filename) = self.process_values(values, preview)
            if aanvraag:
                yield (aanvraag, aanvraag_filename)        
def report_imports(new_aanvragen, preview=False):
    log_info('Rapportage import:', to_console=True)
    if not new_aanvragen:
        new_aanvragen = []
    sop_aanvragen = sop(len(new_aanvragen), "aanvraag", "aanvragen", False)    
    if len(new_aanvragen):
        log_info(f'\t--- Nieuwe {sop_aanvragen} --- :')
        for aanvraag in new_aanvragen:
            log_print(f'\t{str(aanvraag)}')
    log_info(f'\t{len(new_aanvragen)} nieuwe {sop_aanvragen} {pva(preview, "te importeren", "geimporteerd")}.', to_console=True)

def import_excel_file(xls_filename: str, output_directory: str, storage: AAPAStorage, preview=False)->Tuple[int,int]:
    log_info(f'Start import van excel-file {xls_filename}...', to_console=True)
    importer = AanvraagCreatorPipeline(f'Importeren aanvragen uit Excel-bestand {xls_filename}', 
                                     AanvragenFromExcelImporter(output_directory, storage), 
                                     storage, activity = UndoLog.Action.SCAN)
    first_id = storage.find_max_id('aanvragen') + 1
    log_debug(f'first_id: {first_id}')
    (n_processed, n_files) = importer.process([xls_filename], preview=preview)    
    queries:AanvraagQueries = storage.queries('aanvragen')
    new_aanvragen = queries.find_new_aanvragen(first_id=first_id)
    report_imports(new_aanvragen, preview=preview)
    log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(new_aanvragen, "nieuwe aanvraag", "nieuwe aanvragen")} gelezen uit bestand {xls_filename}', to_console=True)
    log_debug(MAJOR_DEBUG_DIVIDER)
    return n_processed, n_files      