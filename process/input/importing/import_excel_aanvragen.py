from tempfile import TemporaryDirectory
from time import sleep
from enum import IntEnum
from pathlib import Path
from mailmerge import MailMerge
from typing import Any, Iterable, Tuple
from data.classes.bedrijven import Bedrijf
from data.general.const import UNKNOWN_STUDNR
from data.classes.studenten import Student

from data.classes.undo_logs import UndoLog
from main.options import AAPAProcessingOptions
from storage.aapa_storage import AAPAStorage
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from storage.queries.aanvragen import AanvragenQueries
from storage.queries.studenten import StudentenQueries
from debug.debug import MAJOR_DEBUG_DIVIDER
from main.log import log_debug, log_error, log_print, log_warning, log_info
from general.pdutil import nrows
from process.general.preview import pva
from general.singular_or_plural import sop
from main.config import IntValueConvertor, config, get_templates
from general.fileutil import created_directory, safe_file_name, set_file_time, test_directory_exists
from general.strutil import replace_all
from general.timeutil import TSC
from process.general.aanvraag_pipeline import AanvraagCreatorPipeline
from process.general.student_dir_builder import SDB
from process.general.word_processor import Word2PdfConvertor
from process.input.importing.aanvraag_importer import AanvraagImporter
from process.input.importing.excel_reader import ExcelReader

def init_config():
    config.init('import', 'xls_template', r'2. Aanvraag goedkeuring afstudeeropdracht nieuwe vorm MAILMERGE 3.00b.docx')
    if template:=config.get('import', 'xls_template'):
        config.set('import', 'xls_template', template.replace('.\\templates\\', ''))
    config.register('import', 'last_id', IntValueConvertor)
    config.init('import', 'last_id', 0)
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
    def __init__(self, output_directory: str, storage: AAPAStorage, last_excel_id = None):
        super().__init__(f'import from excel-file', multiple=True)
        self.template = get_templates(config.get('import', 'xls_template'))
        self.storage = storage
        self.output_directory = output_directory
        self.temp_path = None
        self.last_excel_id = last_excel_id if last_excel_id else config.get('import', 'last_id')
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
    def _get_id(self, values: dict[str,Any])->int:
        return int(self.__get_value(values, self.ColNr.ID))
    def _get_student(self, values:dict[str, Any])->Student:
        result = Student(full_name=self.__get_value(values, self.ColNr.NAAM),
                          stud_nr=self.__get_value(values, self.ColNr.STUDNR),
                          email=self.__get_value(values, self.ColNr.EMAIL))
        student_queries: StudentenQueries = self.storage.queries('studenten')
        if (stored := student_queries.find_student_by_name_or_email_or_studnr(result)):
            result.id = stored.id
            result.status = stored.status
            if stored.stud_nr == UNKNOWN_STUDNR:
                stored.stud_nr = result.stud_nr                
                self.storage.update('studenten', stored)
        else:
            log_info(f'Student {result} is nog niet in database bekend. Wordt nieuw geregistreerd.', to_console=True)
        return result
    def _get_bedrijf(self, values: dict[str,Any])->Bedrijf:
        return Bedrijf(self.__get_value(values, self.ColNr.BEDRIJF))
    def _get_aanvraag(self, values: dict[str, Any])->Aanvraag:
        if (datum_str:=self.__get_value(values, self.ColNr.VOLTOOIEN)) == 'NaT':
            log_info(f'Datum (tijd van voltooien) is niet ingevuld.\nWaarschijnlijk is de student ({self.__get_value(values, self.ColNr.NAAM)}) nog bezig met invullen.')
            return None # not yet completed
        datum = TSC.sortable_str_to_timestamp(datum_str)
        return Aanvraag(self._get_student(values), self._get_bedrijf(values), 
                        datum = datum,
                        datum_str = datum,
                        titel = self.__get_value(values, self.ColNr.TITEL),
                        status=Aanvraag.Status.IMPORTED_XLS
                        )
    def _get_filename_stem(self, aanvraag: Aanvraag)->str:
        return safe_file_name(f'2. Aanvraag Afstuderen {aanvraag.datum}-{aanvraag.student.full_name}-{aanvraag.bedrijf.name}')       
    def get_docx_filename(self, aanvraag: Aanvraag)->str:
        return str(self.temp_path.joinpath(f'{self._get_filename_stem(aanvraag)}.docx'))
    def get_pdf_filename(self, aanvraag: Aanvraag)->str:
        student_directory = Path(SDB.get_student_dir_name(self.storage,aanvraag.student,self.output_directory))
        return str(student_directory.joinpath(f'{self._get_filename_stem(aanvraag)}.pdf'))
    def convert_values(self, values: dict[str, Any])->Tuple[Aanvraag,str,str]:
        #return (aanvraag, docx_filename, pdf_filename)
        NONINO = (None,None,None)
        log_debug(f'Start convert_values: {self.__get_value(values, self.ColNr.NAAM)}')
        try:
            if (aanvraag := self._get_aanvraag(values)):                   
                log_info(f'\t{aanvraag.student.full_name}:', to_console=True)
                if stored := self._existing_aanvraag(aanvraag):
                    log_warning(f'Aanvraag {stored}\n\tal in database. Wordt overgeslagen.')
                    return NONINO
                return aanvraag, self.get_docx_filename(aanvraag), self.get_pdf_filename(aanvraag)
        except Exception as E:
            log_debug(f'Error in convert_values: {E}')
        return NONINO
    def create_docx_file(self, values: dict[str, Any], docx_filename: str, preview=False):
        if not preview:
            merge_dict = {field: str(values.get(self.find_merge_field_vraag(field), '?')) 
                          for field in self.merge_fields}
            with MailMerge(self.template) as document:
                document.merge(**merge_dict)
                document.write(str(docx_filename))
    def create_pdf_file(self, aanvraag: Aanvraag, docx_filename, pdf_filename: str, preview=False)->str:
        student_directory = Path(pdf_filename).parent
        if not test_directory_exists(str(student_directory)):
            if preview:
                log_info(f'Directory {student_directory} aanmaken.')
            else:
                if created_directory(str(student_directory)):
                    log_info(f'Directory {student_directory} aangemaakt.')
                else:
                    log_error(f'Error creating directory {student_directory}')
        if not preview:
            Word2PdfConvertor().convert(docx_filename, pdf_filename)
            set_file_time(pdf_filename, aanvraag.datum)
            # self.files_to_delete.append(Path(docx_filename))
        return pdf_filename
    def _existing_aanvraag(self, aanvraag: Aanvraag)->bool:
        queries: AanvragenQueries = self.storage.queries('aanvragen')
        return queries.find_aanvraag(aanvraag) 
    def create_files(self, aanvraag: Aanvraag, values: dict[str, Any], docx_filename: str, pdf_filename: str, preview=False)->bool:
        log_debug(f'Start create_files: {aanvraag.summary()}')
        try:
            self.create_docx_file(values, docx_filename, preview)
            if not preview:
                sleep(0.3) #small pause, to maybe help sharepoint 
            self.create_pdf_file(aanvraag, docx_filename, pdf_filename, preview)
            log_print(f'Aanvraagbestand {File.display_file(pdf_filename)} {pva(preview, "aanmaken", "aangemaakt")}.')
            return True
        except Exception as E:
            log_debug(f'Error in create_files: {E}')
            return False
    def _find_same_student_aanvraag(self, all_aanvragen: dict[str,Aanvraag], aanvraag: Aanvraag)->dict:
        # email is uniek (en correct omdat dat automatisch door Forms gegenereerd wordt)
        return all_aanvragen.get(aanvraag.student.email, None) 
    def _find_previous_aanvraag(self, all_aanvragen: dict[str,Aanvraag], aanvraag: Aanvraag)->dict:
        if (previous:=self._find_same_student_aanvraag(all_aanvragen, aanvraag)) and previous['aanvraag'].datum < aanvraag.datum:
            return previous
        return None    
    def _find_later_aanvraag(self, all_aanvragen: dict[str, dict], aanvraag: Aanvraag)->dict:
        if (later:=self._find_same_student_aanvraag(all_aanvragen, aanvraag)) and later['aanvraag'].datum > aanvraag.datum:
            return later
        return None    
    def get_aanvragen(self, filename: str)->dict[str,dict]:
        #return form: dict[student.email] = {'values': (values), 'aanvraag': aanvraag, 'docx_filename', 'pdf_filename': pdf_filename}
        reader = ExcelReader(filename, self.ENQUETE_COLUMNS.values())
        if reader.error:
            log_error(f'{reader.error}')
            return {}
        if nrows(reader.dataframe) == 0:
            log_warning(f'Niets om te importeren in {filename}.')
            return {}
        all_aanvragen = {}
        for values in reader.read():
            if (id:=self._get_id(values)) <= self.last_excel_id:
                continue
            aanvraag,docx_filename, pdf_filename = self.convert_values(values)
            if aanvraag:  
                log_print(f'\t\t{aanvraag.datum} - {aanvraag.titel}')                  
                if (previous := self._find_previous_aanvraag(all_aanvragen, aanvraag)):
                    log_warning(f'Nieuwere aanvraag van {aanvraag.student}.\nVorige versie wordt niet in behandeling genomen.')
                    all_aanvragen.pop(previous['aanvraag'].student.email)
                if (later := self._find_later_aanvraag(all_aanvragen, aanvraag)):
                    log_warning(f'Eerder al een nieuwere versie gelezen ({later.summary()}.\nDeze versie wordt niet in behandeling genomen.')
                else:
                    all_aanvragen[aanvraag.student.email] = {'values': values, 'aanvraag': aanvraag, 
                                                            'docx_filename': docx_filename, 
                                                            'pdf_filename': pdf_filename, 'id':id}
        return all_aanvragen
    def read_aanvragen(self, filename: str, preview=False)->Iterable[Tuple[Aanvraag,str]]:
        #return form: dict[student.email] = {'aanvraag': aanvraag, 'docx_filename', 'pdf_filename': pdf_filename}
        with TemporaryDirectory() as tmp:
            self.temp_path = Path(tmp)
            #temporary directory for storing .docx aanvragen
            #these will be saved as .pdf somewhere else, the .docx can be removed after.
            log_debug(f'Start read_aanvragen\n\t{filename}\n\tfirst-id={self.last_excel_id}')
            for n, entry in enumerate(self.get_aanvragen(filename).values()):
                log_debug(f'{n}:{entry["aanvraag"].student.full_name}')
                try:
                    if self.create_files(entry['aanvraag'], entry['values'], entry['docx_filename'], entry['pdf_filename'], preview):
                        self.ids_read.append(entry['id'])
                        yield entry['aanvraag'], entry['pdf_filename']
                except Exception as E:
                    log_debug(f'Error in read_aanvragen:\n{E}')
                    sleep(.5) # hope this helps with sharepoint delays
                    yield (None,None)
    def before_reading(self, preview = False):
        self.ids_read = []

    def after_reading(self, preview = False):
        if preview:
            return
        if self.ids_read:
            config.set('import', 'last_id', max(self.ids_read))

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
def import_excel_file(xls_filename: str, output_directory: str, storage: AAPAStorage, preview=False, last_excel_id=None)->Tuple[int,int]:
    log_info(f'Start import van excel-file {xls_filename}...', to_console=True)
    importer = AanvraagCreatorPipeline(f'Importeren aanvragen uit Excel-bestand {xls_filename}', 
                                     AanvragenFromExcelImporter(output_directory, storage, last_excel_id), 
                                     storage, activity = UndoLog.Action.INPUT)
    first_aanvraag_id = storage.find_max_id('aanvragen') + 1
    log_debug(f'first_id: {first_aanvraag_id}')
    (n_processed, n_files) = importer.process([xls_filename], preview=preview)    
    queries:AanvragenQueries = storage.queries('aanvragen')
    new_aanvragen = queries.find_new_aanvragen(first_id=first_aanvraag_id)
    report_imports(new_aanvragen, preview=preview)
    log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(len(new_aanvragen), "nieuwe aanvraag", "nieuwe aanvragen")} {pva(preview,"te lezen", "gelezen")} uit bestand {xls_filename})', to_console=True)
    log_debug(MAJOR_DEBUG_DIVIDER)
    return len(new_aanvragen), n_files      