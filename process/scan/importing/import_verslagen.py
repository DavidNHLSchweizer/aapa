from pathlib import Path
import re
from data.classes.const import MijlpaalType
from data.classes.files import File
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.studenten import StudentQueries
from general.fileutil import summary_string
from general.log import log_debug, log_info, log_print, log_warning
from general.singular_or_plural import sop
from process.general.verslag_pipeline import VerslagCreatingPipeline
from process.general.verslag_processor import MijlpaalCreator
from process.general.zipfile_reader import ZipFileReader
from process.scan.importing.filename_in_zip_parser import FilenameInZipParser

class VerlagParseException(Exception): pass

class VerslagFromZipImporter(MijlpaalCreator):
    def __init__(self, description = ''):
        super().__init__(description=description)
        self.parser = FilenameInZipParser()

    def create_from_parsed(self, storage: AAPAStorage, filename: str, parsed: FilenameInZipParser.Parsed)->Verslag:
        VerslagTypes = {'plan van aanpak': MijlpaalType.PVA, 
                        'onderzoeksverslag': MijlpaalType.ONDERZOEKS_VERSLAG, 
                        'technisch verslag': MijlpaalType.TECHNISCH_VERSLAG, 
                        'eindverslag': MijlpaalType.EIND_VERSLAG}
        def get_verslag_type(product_type: str)->MijlpaalType:
            if (result := VerslagTypes.get(product_type.lower(), None)):
                return result
            raise VerlagParseException(f'Onbekend verslagtype: {[product_type]}')
        def get_kans(kans_decription: str)->int:
            KANSPATTERN = r'(?<n>[\d]+).*kans'
            match kans_decription:
                case '1e kans': return 1
                case 'herkansing': return 2
                case re.match(KANSPATTERN, kans_decription):
                    return re.match(KANSPATTERN).group('n')
                case _: return 0

        def get_student(storage: AAPAStorage, student_name: str, email: str)->Student:
            storage_queries: StudentQueries = storage.queries('studenten')
            student = Student(full_name=student_name, email=email)
            stored:Student = storage_queries.find_student_by_name_or_email(student=student)
            if stored:                 
                return stored
            student.stud_nr = storage_queries.create_unique_student_nr(student=student)
            log_warning(f'Student {student_name} niet gevonden in database. Gebruik fake studentnummer {student.stud_nr}')
            return student            
        return Verslag(mijlpaal_type=get_verslag_type(parsed.product_type), student=get_student(storage, parsed.student_name, email=parsed.email), 
                       file=File(filename), datum=parsed.datum, kans=get_kans(parsed.kans), titel=Path(parsed.original_filename).stem)  
    def process_file(self, filename: str, storage: AAPAStorage, preview=False, **kwargs)->Verslag:
        log_print(f'Laden uit zipfile: {summary_string(filename, maxlen=100)}')
        try:      
            if parsed:=self.parser.parsed(filename):
                new_filename = f'temp_placeholder {parsed.original_filename}'
                verslag = self.create_from_parsed(storage, new_filename, parsed)
                log_print(f'\t{str(verslag)}:\n\t{summary_string(new_filename)}')
                return verslag
        except VerlagParseException as parser_exception:
            log_warning(f'{parser_exception}.') 
        return None

class VerslagenImporter(VerslagCreatingPipeline): pass

def import_zipfile(zip_filename: str, output_directory: str, storage: AAPAStorage, preview=False)->int:
    log_info(f'Start import uit zipfile {zip_filename}...', to_console=True)
    importer = VerslagenImporter(f'Importeren verslagen uit zip-file {zip_filename}', VerslagFromZipImporter(), storage)
    first_id = storage.find_max_id('verslagen') + 1
    log_debug(f'first_id: {first_id}')
    reader = ZipFileReader()
    reader.read_info(zip_filename=zip_filename)
    (n_processed, n_files) = importer.process(reader.filenames, preview=preview)
    # report_imports(importer.storage.aanvragen.read_all(lambda a: a.id >= first_id), preview=preview)
    log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(n_processed, "nieuw verslag", "nieuwe verslagen")}.', to_console=True)
    return n_processed, n_files      