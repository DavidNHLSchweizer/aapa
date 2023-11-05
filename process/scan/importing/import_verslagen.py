from pathlib import Path
import re
from data.classes.files import File
from data.classes.milestones import StudentMilestone
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.storage import AAPAStorage
from general.fileutil import summary_string
from general.log import log_debug, log_info, log_print, log_warning
from general.singular_or_plural import sop
from process.general.verslag_pipeline import VerslagCreatingPipeline
from process.general.verslag_processor import VerslagCreator
from process.general.zipfile_reader import ZipFileReader
from process.scan.importing.filename_parser import FilenameParser

class VerslagParseException(Exception): pass

class VerslagFromZipImporter(VerslagCreator):
    def __init__(self, description = ''):
        super().__init__(description=description)
        self.parser = FilenameParser()

    def create_from_parsed(self, storage: AAPAStorage, filename: str, parsed: FilenameParser.Parsed)->Verslag:
        VerslagTypes = {'plan van aanpak': StudentMilestone.Type.PVA, 
                        'onderzoeksverslag': StudentMilestone.Type.ONDERZOEKS_VERSLAG, 
                        'technisch verslag': StudentMilestone.Type.TECHNISCH_VERSLAG, 
                        'eindverslag': StudentMilestone.Type.EIND_VERSLAG}
        def get_verslag_type(product_type: str)->StudentMilestone.Type:
            if (result := VerslagTypes.get(product_type.lower(), None)):
                return result
            raise VerslagParseException(f'Onbekend verslagtype: {[product_type]}')
        def get_kans(kans_decription: str)->int:
            KANSPATTERN = '(?<n>[\d]+).*kans'
            match kans_decription:
                case '1e kans': return 1
                case 'herkansing': return 2
                case re.match(KANSPATTERN, kans_decription):
                    return re.match(KANSPATTERN).group('n')
                case _: return 0

        def get_student(storage: AAPAStorage, student_name: str, email: str)->Student:
            student = Student(full_name=student_name, email=email)
            if (stored := storage.studenten.find_student_by_name_or_email(student)):                
                return stored
            student.stud_nr = storage.studenten.create_unique_student_nr(student)
            log_warning(f'Student {student_name} niet gevonden in database. Gebruik fake studentnummer {student.stud_nr}')
            return student            
        return Verslag(verslag_type=get_verslag_type(parsed.product_type), student=get_student(storage, parsed.student_name, email=parsed.email), 
                       file=File(filename), datum=parsed.datum, kans=get_kans(parsed.kans), titel=Path(parsed.original_filename).stem)  
    def process_file(self, filename: str, storage: AAPAStorage, preview=False, **kwargs)->Verslag:
        log_print(f'Laden uit zipfile: {summary_string(filename, maxlen=100)}')
        try:      
            if parsed:=self.parser.parsed(filename):
                new_filename = f'temp_placeholder {parsed.original_filename}'
                verslag = self.create_from_parsed(storage, new_filename, parsed)
                log_print(f'\t{str(verslag)}:\n\t{summary_string(new_filename)}')
                return verslag
        except VerslagParseException as parser_exception:
            log_warning(f'{parser_exception}.') 
        return None

class VerslagenImporter(VerslagCreatingPipeline): pass

def import_zipfile(zip_filename: str, output_directory: str, storage: AAPAStorage, preview=False)->int:
    log_info(f'Start import uit zipfile {zip_filename}...', to_console=True)
    importer = VerslagenImporter(f'Importeren verslagen uit zip-file {zip_filename}', VerslagFromZipImporter(), storage)
    
    first_id = storage.aanvragen.max_id() + 1
    reader = ZipFileReader()
    reader.read_info(zip_filename=zip_filename)
    (n_processed, n_files) = importer.process(reader.filenames, preview=preview)
    # report_imports(importer.storage.aanvragen.read_all(lambda a: a.id >= first_id), preview=preview)
    log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(n_processed, "nieuw verslag", "nieuwe verslagen")}.', to_console=True)
    return n_processed, n_files      