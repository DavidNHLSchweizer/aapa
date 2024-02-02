from pathlib import Path
from time import sleep
from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.aanvragen import AanvraagQueries
from data.storage.queries.student_directories import StudentDirectoryQueries
from data.storage.queries.studenten import StudentQueries
from general.fileutil import file_exists, last_parts_file
from general.log import log_debug, log_print, log_warning
from process.general.student_dir_builder import StudentDirectoryBuilder
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
    def _get_kans(self, student: Student, mijlpaal_type: MijlpaalType)->int:
        storage_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        mijlpalen = storage_queries.find_student_mijlpaal_dir(student, mijlpaal_type)
        return 1 + len(mijlpalen)
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
        kans=self._get_kans(student, mijlpaal_type)
        titel=Path(parsed.original_filename).stem
        return Verslag(mijlpaal_type=mijlpaal_type, student=student,datum=parsed.datum,bedrijf=bedrijf,kans=kans,titel=titel)
    def get_verslagen(self, zip_filename: str)->dict[str, list[dict[Verslag,str,str,str]]]:
        #return per student (indexed on email): list of {verslag object, filename in zip, original filename}
        self.reader.parse(zip_filename=zip_filename)  
        result = {}
        for parsed in self.reader.parsed_list:
            verslag = self._get_verslag_from_parsed(parsed)
            student_key = verslag.student.email
            student_entries = result.get(student_key, [])
            student_entries.append({'verslag': verslag, 
                                  'filename_in_zip': parsed.filename_in_zip, 
                                  'original_filename': parsed.original_filename,
                                  'filename_to_create': self.get_filename_to_create(verslag, parsed.original_filename)
                                  })
            result[student_key] = student_entries
        for student_entries in result.values():
            if len(student_entries)>1:
                for entry in student_entries:
                    entry['verslag'].status = Verslag.Status.MULTIPLE
        return result
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
    def _check_existing_files(self, student_entries: list[dict]):
        previous_existing = False
        for student_entry in student_entries:
            filename_to_create = student_entry['filename_to_create']
            student_entry['existing'] = file_exists(filename_to_create)
            if student_entry['existing']:
                previous_existing = True
                student_entry['verslag'].status = Verslag.Status.LEGACY
        if previous_existing:
            for student_entry in student_entries:
                student_entry['verslag'].kans -= 1
    def read_verslagen(self, zip_filename: str, preview: bool)->Iterable[Verslag]:
        #return generator ("list") of verslag objects
        log_debug(f'Start read_verslagen\n\t{zip_filename}')
        for student_entries in self.get_verslagen(zip_filename).values():
            try:
                self._check_existing_files(student_entries)
                new_student = True
                for student_entry in student_entries:                    
                    verslag = student_entry['verslag']
                    filename_to_create = student_entry['filename_to_create']
                    log_debug(f'filename to create: {filename_to_create}')
                    if student_entry['existing']:
                        log_warning(f'Bestand {last_parts_file(filename_to_create)}\n\tbestaat al. Wordt overgeslagen (aanname: dit verslag is al eerder op sharepoint geplaatst).\n\tWordt wel opgenomen in database.')
                    else:
                        file = self.create_file(student_entry['filename_in_zip'], filename_to_create, new_student, preview=preview)
                #hier: doe hier nog  iets mee (registeren?)                
                    new_student = False
                    yield verslag
            except Exception as E:
                log_debug(f'Error in read_verslagen:\n{E}')
                sleep(.5) # hope this helps with sharepoint delays
                yield None
