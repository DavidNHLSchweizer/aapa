from pathlib import Path
from time import sleep
from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.general.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from storage.aapa_storage import AAPAStorage
from storage.queries.aanvragen import AanvraagQueries
from storage.queries.files import FilesQueries
from storage.queries.student_directories import StudentDirectoryQueries
from storage.queries.studenten import StudentQueries
from general.fileutil import file_exists
from main.config import config
from main.log import log_debug, log_error, log_info, log_print, log_warning
from process.general.student_dir_builder import SDB, StudentDirectoryBuilder
from process.general.verslag_processor import VerslagImporter
from process.general.zipfile_reader import BBFilenameInZipParser, BBZipFileReader
from storage.queries.verslagen import VerslagQueries

class VerslagParseException(Exception): pass

class VerslagFromZipImporter(VerslagImporter):
    def __init__(self, root_directory: str, storage: AAPAStorage):
        super().__init__(f'import from zip-file', multiple=True)
        self.storage = storage
        self.sdb = SDB(storage)
        self.reader = BBZipFileReader()
        self.root_directory = root_directory
        self.verslag_queries:VerslagQueries = self.storage.queries('verslagen')
        self.student_directory_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        self.studenten_queries: StudentQueries = self.storage.queries('studenten')
        self.aanvraag_queries:AanvraagQueries = self.storage.queries('aanvragen')
        self.files_queries: FilesQueries = self.storage.queries('files')

    def _get_verslag_type(self, product_type: str)->MijlpaalType:
        VerslagTypes = {'plan van aanpak': MijlpaalType.PVA, 
                        'onderzoeksverslag': MijlpaalType.ONDERZOEKS_VERSLAG, 
                        'technisch verslag': MijlpaalType.TECHNISCH_VERSLAG, 
                        'eindverslag': MijlpaalType.EIND_VERSLAG}
        if (result := VerslagTypes.get(product_type.lower(), None)):
            return result
        raise VerslagParseException(f'Onbekend verslagtype: {[product_type]}')
    def _get_kans(self, student: Student, mijlpaal_type: MijlpaalType)->int:
        mijlpalen = self.student_directory_queries.find_student_mijlpaal_dir(student, mijlpaal_type)
        return 1 + len(mijlpalen)
    def _get_student(self, student_name: str, email: str)->Student:
        
        student = Student(full_name=student_name, email=email)
        stored:Student = self.studenten_queries.find_student_by_name_or_email_or_studnr(student=student)
        if stored:                 
            return stored
        log_warning(f'Student {student.full_name} is nog niet bekend in database. Dit wordt NIET verwacht!\nDefault waarden (zoals fake studentnummer) worden gebruikt,\nmaar controleer de database vóór verder te gaan!')
        student.stud_nr = self.studenten_queries.create_unique_student_nr(student=student)
        return student            
    def _get_bedrijf(self, student: Student)->Bedrijf:
        aanvraag = self.aanvraag_queries.find_student_aanvraag(student)
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
        for parsed in sorted(self.reader.parsed_list,key=lambda p: p.student_name):
            verslag = self._get_verslag_from_parsed(parsed)
            log_print(f'Student: {verslag.student.full_name}')
            student_key = verslag.student.email
            student_entries = result.get(student_key, [])
            student_entries.append({'verslag': verslag, 
                                  'filename_in_zip': parsed.filename_in_zip, 
                                  'original_filename': parsed.original_filename,
                                  'filename_to_create': self.get_filename_to_create(verslag, parsed.original_filename)
                                  })
            log_print(f'\t{parsed.original_filename}: {verslag.mijlpaal_type}')
            result[student_key] = student_entries
        for student_entries in result.values():
            if len(student_entries)>1:                
                for entry in student_entries:                    
                        entry['verslag'].status = Verslag.Status.NEW_MULTIPLE
        return result
    def get_filename_to_create(self, verslag: Verslag, original_filename: str):
        student_directory = SDB.get_student_dir(self.storage,verslag.student,self.root_directory)
        if mp_dir := student_directory.get_directory(verslag.datum, verslag.mijlpaal_type, config.get('directories', 'error_margin_date')):
            directory = mp_dir.directory
            verslag.kans = mp_dir.kans
        else:
            directory = StudentDirectoryBuilder.get_mijlpaal_directory_name(student_directory, verslag.datum, verslag.mijlpaal_type)
        mijlpaal_directory:MijlpaalDirectory = self.sdb.get_mijlpaal_directory(stud_dir=student_directory, directory=directory, 
                                                                          datum=verslag.datum, mijlpaal_type=verslag.mijlpaal_type, 
                                                                          error_margin=4.0)
        return str(Path(mijlpaal_directory.directory).joinpath(original_filename))
    def created_directory(self, directory_path: Path, preview: bool)->bool:
        if preview:
            return True
        elif not directory_path.is_dir():
            directory_path.mkdir()
            return True
        return False
    def _check_in_database(self, student_directory:StudentDirectory, filename_to_create: str)->bool:        
        for file in student_directory.get_files():
            if file.filename.lower() == filename_to_create.lower():
                return True
        # if we get here, try a good-luck search. Hopefully the database is not out-of-sync with reality        
        return self.files_queries.is_known_file(filename_to_create)
    
    def _register_verslag(self, verslag: Verslag, filename: str):
        file = verslag.register_file(filename, verslag.mijlpaal_type.default_filetype(), verslag.mijlpaal_type)
        self.sdb.register_file(student=verslag.student, datum=file.timestamp if file_exists(filename) else verslag.datum,
                                        filename=filename, filetype=file.filetype, mijlpaal_type=file.mijlpaal_type)

    def _create_file(self, verslag: Verslag, mp_dir: MijlpaalDirectory, filename_in_zip: str, filename_to_create: str, new_student:bool, preview=False):
        mijlpaal_directory_path = Path(mp_dir.directory) if mp_dir else Path(filename_to_create).parent
        # if mp_dir:



        if preview:
            if not mijlpaal_directory_path.is_dir() and new_student:
                if mp_dir:
                    log_warning(f'Directory {File.display_file(mijlpaal_directory_path)} in database, maar bestaat niet in filesysteem.')
                log_print(f'\tDirectory aanmaken {File.display_file(mijlpaal_directory_path)}')
            log_print(f'\tBestand aanmaken {File.display_file(filename_to_create)}')                
        else:
            if mp_dir and not mijlpaal_directory_path.is_dir():
                log_warning(f'Directory {File.display_file(mijlpaal_directory_path)} in database, maar bestaat niet in filesysteem.')
            if self.created_directory(mijlpaal_directory_path, preview):
                log_print(f'\tDirectory {File.display_file(mijlpaal_directory_path)} aangemaakt')
            self.reader.extract_file(filename_in_zip, mijlpaal_directory_path, Path(filename_to_create).name)
            log_print(f'\tBestand {File.display_file(filename_to_create)} aangemaakt.')
        self._register_verslag(verslag, filename_to_create)
    def _check_existing_files(self, student_entries: list[dict]):
        previous_existing = False
        # because filename comparisons are difficult to get REALLY caseinsensitive in SQLite 
        # (collating only works for standard ASCII, and some students have non-ascii names)
        # we must do this in python
        if student_entries: #get the student from the first entry
            student_directory = self.student_directory_queries.find_student_dir(student_entries[0]['verslag'].student)
        else:
            student_directory = None
        for student_entry in student_entries:
            filename_to_create = student_entry['filename_to_create']
            student_entry['student_directory'] = student_directory
            student_entry['stored'] = self._check_in_database(student_directory, filename_to_create=filename_to_create)
            student_entry['mp_dir'] = student_directory.get_filename_directory(filename_to_create) if student_directory else None
            student_entry['existing'] = file_exists(filename_to_create)
            if student_entry['existing'] or student_entry['stored']:
                previous_existing = True
                student_entry['verslag'].status = Verslag.Status.LEGACY
        if previous_existing:
            for student_entry in student_entries:
                if student_entry['mp_dir']:
                    student_entry['verslag'].kans = student_entry['mp_dir'].kans
                else:
                    student_entry['verslag'].kans -= 1
    def _find_mp_dir(self, verslag: Verslag)->MijlpaalDirectory:
        target_dir = verslag.get_directory()
        for mp_dir in self.student_directory_queries.find_student_mijlpaal_dir(verslag.student, verslag.mijlpaal_type):
            if str(mp_dir.directory) == target_dir:
                return mp_dir
        return None
    def _check_existing_verslag(self, student_directory: StudentDirectory, filename_to_create: str)->Verslag:
        if not student_directory:
            return None
        if mp_dir := student_directory.get_filename_directory(filename_to_create):
            known_verslagen = self.verslag_queries.find_values(['student', 'mijlpaal_type', 'kans'], [student_directory.student,mp_dir.mijlpaal_type, mp_dir.kans], map_values = True, read_many=False)
            return known_verslagen[0] if known_verslagen else None
        # self.storage.queries('mijlpaal_directories').find_verslag(mp_dir)
    def _process_student_entry(self, current_verslag: Verslag, student_entry: dict, preview=False)->Verslag:
        overgeslagen = 'Wordt overgeslagen.'
        new_verslag:Verslag = student_entry['verslag']
        if current_verslag and new_verslag.mijlpaal_type == current_verslag.mijlpaal_type and current_verslag.student==new_verslag.student:
            new_verslag = current_verslag
        filename_to_create = student_entry['filename_to_create']
        stored_verslag = self._check_existing_verslag(student_entry['student_directory'], filename_to_create)
        log_debug(f'filename to create: {filename_to_create}')   
        if stored_verslag:
            log_warning(f'Verslag {stored_verslag.summary()} is al geregistreerd in de database.')
            if not stored_verslag.files.find_filename(filename_to_create):
                stored_verslag.register_file(filename_to_create,filetype=stored_verslag.mijlpaal_type.default_filetype(), mijlpaal_type=stored_verslag.mijlpaal_type)                    
                new_verslag = stored_verslag
        if student_entry['stored'] and student_entry['existing']:
            log_warning(f'Bestand {File.display_file(filename_to_create)}\n\t bestaat al en is in database bekend. {overgeslagen}')
            return None
        elif student_entry['existing']:
            log_warning(f'Bestand {File.display_file(filename_to_create)}\n\tbestaat al. {overgeslagen}')
            return None
        if not stored_verslag:
            self._create_file(new_verslag, student_entry['mp_dir'], student_entry['filename_in_zip'], 
                              filename_to_create, new_student=current_verslag is None, preview=preview)
        return new_verslag
        
    def read_verslagen(self, zip_filename: str, preview: bool)->Iterable[Verslag]:
        #return generator ("list") of verslag objects
        log_debug(f'Start read_verslagen\n\t{zip_filename}')
        first = True
        for student_entries in self.get_verslagen(zip_filename).values():
            if first:
                log_info('Start aanmaken bestanden en directories', to_console=True)
                first = False
            try:
                self._check_existing_files(student_entries)
                verslag = None
                for student_entry in student_entries:                    
                    verslag = self._process_student_entry(verslag, student_entry, preview)
                if verslag:
                    yield verslag
            except Exception as E:
                log_error(f'Error in read_verslagen:\n{E}')
                sleep(.25) # hope this helps with sharepoint delays
                yield None
