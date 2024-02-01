from pathlib import Path
import re
from time import sleep
from typing import Iterable, Tuple
from data.classes.bedrijven import Bedrijf
from data.classes.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.classes.undo_logs import UndoLog
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.aanvragen import AanvraagQueries
from data.storage.queries.studenten import StudentQueries
from debug.debug import MAJOR_DEBUG_DIVIDER
from general.fileutil import last_parts_file, summary_string, test_directory_exists
from general.log import log_debug, log_error, log_info, log_print, log_warning
from general.singular_or_plural import sop
from process.general.student_dir_builder import StudentDirectoryBuilder
from process.general.verslag_pipeline import VerslagCreatingPipeline
from process.general.verslag_processor import VerslagImporter
from process.general.zipfile_reader import BBFilenameInZipParser, BBZipFileReader

class VerlagParseException(Exception): pass

class VerslagFromZipImporter(VerslagImporter):
    def __init__(self, root_directory: str, storage: AAPAStorage):
        super().__init__(f'import from zip-file', multiple=True)
        self.storage = storage
        self.reader = BBZipFileReader()
        self.root_directory = root_directory

    def _get_verslag_type(self, product_type: str)->MijlpaalType:
        VerslagTypes = {'plan van aanpak': MijlpaalType.PVA, 
                        'onderzoeksverslag': MijlpaalType.ONDERZOEKS_VERSLAG, 
                        'technisch verslag': MijlpaalType.TECHNISCH_VERSLAG, 
                        'eindverslag': MijlpaalType.EIND_VERSLAG}
        if (result := VerslagTypes.get(product_type.lower(), None)):
            return result
        raise VerlagParseException(f'Onbekend verslagtype: {[product_type]}')
    def _get_kans(self, kans_decription: str)->int:
        match kans_decription:
            case '1e kans': 
                return 1
            case 'herkansing'|'2e kans': 
                return 2
            case _: 
                return 0                    
    def _get_student(self, student_name: str, email: str)->Student:
        storage_queries: StudentQueries = self.storage.queries('studenten')
        student = Student(full_name=student_name, email=email)
        stored:Student = storage_queries.find_student_by_name_or_email_or_studnr(student=student)
        if stored:                 
            return stored
        log_warning(f'Student {student.full_name} is nog niet bekend in database. Dit wordt NIET verwacht!\nDefault waarden (zoals fake studentnummer) worden gebruikt,\nmaar controleer de database vóór verder te gaan!')
        student.stud_nr = storage_queries.create_unique_student_nr(student=student)
        return student            
    def _get_bedrijf(self, student: Student)->Bedrijf:
        aanvraag_queries:AanvraagQueries = self.storage.queries('aanvragen')
        aanvraag = aanvraag_queries.find_student_aanvraag(student)
        if not aanvraag:
            log_warning(f'Afstudeerbedrijf kan niet worden gevonden: Geen aanvraag gevonden voor student {student}.')
            return None
        return aanvraag.bedrijf
    def _get_verslag_from_parsed(self, parsed: BBFilenameInZipParser.Parsed)->Verslag:
        mijlpaal_type=self._get_verslag_type(parsed.product_type)
        student=self._get_student(parsed.student_name, email=parsed.email)
        bedrijf=self._get_bedrijf(student)
        kans=self._get_kans(parsed.kans)
        titel=Path(parsed.original_filename).stem
        verslag = Verslag(verslag_type=mijlpaal_type, student=student,datum=parsed.datum,bedrijf=bedrijf,kans=kans,titel=titel)
        return verslag
        return Verslag(verslag_type=self._get_verslag_type(parsed.product_type), student=self._get_student(parsed.student_name, email=parsed.email), 
                       datum=parsed.datum, kans=self._get_kans(parsed.kans), titel=Path(parsed.original_filename).stem)  
    def get_verslagen(self, zip_filename: str)->list[Tuple[Verslag,str,str]]:
        #return verslag object, filename in zip, original filename
        self.reader.parse(zip_filename=zip_filename)  
        result = []
        for parsed in self.reader.parsed_list:
            verslag = self._get_verslag_from_parsed(parsed)
            result.append((verslag,parsed.filename_in_zip, parsed.original_filename))
        return result

        # return [(self._get_verslag_from_parsed(parsed), parsed.filename_in_zip, parsed.original_filename) for parsed in self.reader.parsed_list]

    def get_filename_to_create(self, verslag: Verslag, original_filename: str):
        student_directory = Path(StudentDirectoryBuilder.get_student_dir_name(self.storage,verslag.student,self.root_directory))        
        mijlpaal_directory = student_directory.joinpath(MijlpaalDirectory.directory_name(verslag.mijlpaal_type, verslag.datum))
        return str(mijlpaal_directory.joinpath(original_filename))
    def created_directory(self, directory_path: Path)->bool:
        if not directory_path.is_dir():
            directory_path.mkdir()
            return True
        return False
    def create_file(self, filename_in_zip: str, filename_to_create: str, new_student:bool, preview=False)->File:
        mijlpaal_directory = Path(filename_to_create).parent
        if preview:
            if not mijlpaal_directory.is_dir() and new_student:
                log_print(f'\tAanmaken directory {last_parts_file(mijlpaal_directory)}')
            log_print(f'\tOntzippen {last_parts_file(filename_to_create)}')                
            return File(filename_to_create)
        else:
            mijlpaal_directory = Path(filename_to_create).parent
            if self.created_directory(mijlpaal_directory):
                log_print(f'\tDirectory {last_parts_file(mijlpaal_directory)} aangemaakt')
            filename = self.reader.extract_file(filename_in_zip, mijlpaal_directory)
            log_print(f'\tBestand {last_parts_file(filename_to_create)} aangemaakt.')
            return File(filename)
    def read_verslagen(self, zip_filename: str, preview: bool)->Iterable[Verslag]:
        #return generator ("list") of verslag objects
        log_debug(f'Start read_verslagen\n\t{zip_filename}')
        current_student = None
        for n, (verslag, filename_in_zip, original_filename) in enumerate(self.get_verslagen(zip_filename)):
            log_debug(f'READ_VERSLAGEN {n}: {original_filename} ({filename_in_zip})')
            try:
                filename_to_create = self.get_filename_to_create(verslag, original_filename)
                log_debug(f'filename to create: {filename_to_create}')
                if not current_student or verslag.student != current_student:
                    log_info(f'{verslag.student}:', to_console=True)
                    current_student = verslag.student
                    new_student = True
                else:
                    new_student = False
                file = self.create_file(filename_in_zip, filename_to_create, new_student, preview=preview)
                #hier: doe hier nog  iets mee (registeren)                
                yield verslag
            except Exception as E:
                log_debug(f'Error in read_verslagen:\n{E}')
                #sleep(.5) # hope this helps with sharepoint delays
                yield None

    # def process_file(self, filename: str, storage: AAPAStorage, preview=False, **kwargs)->Verslag:
    #     log_print(f'Laden uit zipfile: {summary_string(filename, maxlen=100)}')
    #     try:      
    #         if parsed:=self.parser.parsed(filename):
    #             new_filename = f'temp_placeholder {parsed.original_filename}'
    #             verslag = self.create_from_parsed(storage, new_filename, parsed)
    #             log_print(f'\t{str(verslag)}:\n\t{summary_string(new_filename)}')
    #             return verslag
    #     except VerlagParseException as parser_exception:
    #         log_warning(f'{parser_exception}.') 
    #     return None

# class VerslagenImporter(VerslagCreatingPipeline): pass

# def import_zipfile(zip_filename: str, root_directory: str, storage: AAPAStorage, preview=False)->int:
#     log_info(f'Start import uit zipfile {zip_filename}...', to_console=True)
#     importer = VerslagenImporter(f'Importeren verslagen uit zip-file {zip_filename}', VerslagFromZipImporter(root_directory=root_directory, storage=storage), storage)
#     first_id = storage.find_max_id('verslagen') + 1
#     log_debug(f'first_id: {first_id}')
#     reader = ZipFileReader()
#     reader.read_info(zip_filename=zip_filename)
#     (n_processed, n_files) = importer.process(reader.filenames, preview=preview)
#     log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
#     log_info(f'...Import afgerond ({sop(n_processed, "nieuw verslag", "nieuwe verslagen")}.', to_console=True)
#     return n_processed, n_files      

