""" DETECT_STUDENT_FROM_DIRECTORY

    Genereert SQL-code om een directory te scannen en alle studentgegevens in de database 
    te importeren. 
        
    De resultaten worden .json  weggeschreven.

    De gegeneerde SQL-code kan met "run_extra.py json" worden uitgevoerd.

"""
#TODO: testen na overzetten Plugin. Heeft geen haast

from argparse import ArgumentParser
from pathlib import Path
from typing import Any
from data.general.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.undo_logs import UndoLog
from data.classes.base_dirs import BaseDir
from data.classes.studenten import Student
from general.sql_coll import SQLcollector, SQLcollectors
from data.general.roots import Roots
from main.options import AAPAProcessingOptions
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirsQueries
from storage.queries.studenten import StudentenQueries
from general.fileutil import test_directory_exists
from main.log import log_debug, log_error, log_info, log_print, log_warning
from general.singular_or_plural import sop
from general.timeutil import TSC
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from process.general.base_processor import FileProcessor
from process.general.pipeline import FilePipeline
from process.input.importing.dirname_parser import DirectoryNameParser
from process.input.importing.filename_parser import FileTypeDetector

SKIP_DIRECTORIES = ['01 Formulieren', 'aapa', 'Beoordeling aanvragen 2023']

class DetectorException(Exception): pass

class StudentDirectoryDetector(FileProcessor):
    ERRCOMMENT= 'Directory kan niet worden herkend'
    def __init__(self):
        super().__init__(description='StudentDirectory Detector')
        self.parser = DirectoryNameParser()
        self.filetype_detector = FileTypeDetector()
        self.base_dir: BaseDir = None
        self.current_student_directory: StudentDirectory = None
        self.new_students:dict[int:Student] = {}
    
    def _get_student(self, student_directory: str, storage: AAPAStorage)->Student:
        if not (parsed := self.parser.parsed(student_directory)):
            raise DetectorException(f'directory {File.display_file(student_directory)} kan niet worden herkend.')
        student = Student(full_name=parsed.student,email=parsed.email())
        queries: StudentenQueries = storage.queries('studenten')
        if storage and (stored := queries.find_student_by_name_or_email_or_studnr(student)):
            return stored
        storage.ensure_key('studenten',student)
        self.new_students[student.id] = student
        return student
    # def _get_aanvraag(self, student: Student, storage: AAPAStorage)->Aanvraag:
    #     if student.id == EMPTY_ID:
    #         return None
    #     if max_id := storage.find_max_value('aanvragen', attribute='id', where_attributes='student', where_values=student.id):
    #         return storage.read('aanvragen', max_id)
    def _get_basedir(self, dirname: str, storage: AAPAStorage)->BaseDir:
        queries : BaseDirsQueries = storage.queries('base_dirs')
        self.base_dir = queries.find_basedir(dirname)
        return self.base_dir != None
    def _parse_type(self, subdirectory:str, parsed_type: str)->MijlpaalType:
        match parsed_type.lower():
            case 'pva' | 'plan van aanpak': return MijlpaalType.PVA
            case 'onderzoeksverslag'|'onderzoek': return MijlpaalType.ONDERZOEKS_VERSLAG
            case 'technisch verslag': return MijlpaalType.TECHNISCH_VERSLAG
            case 'eindverslag': return MijlpaalType.EIND_VERSLAG
            case 'product' | 'productbeoordeling': return MijlpaalType.PRODUCT_BEOORDELING
            case 'afstudeerzitting': return MijlpaalType.EINDBEOORDELING
            case _:                 
                if parsed_type:
                    if type_str := self.parser.parse_non_standard(subdirectory, parsed_type):
                        return self._parse_type(subdirectory, type_str)
                    else:
                        log_warning(f'Soort directory "{parsed_type}" niet herkend.')
                else:
                    log_warning(f'Directory {Path(subdirectory).name} niet herkend.')
        return None
    def _collect_files(self, new_dir: MijlpaalDirectory):
        for filename in Path(new_dir.directory).glob('*'):
            if not filename.is_file():
                continue
            log_debug(f'collecting {filename}')
            filetype,mijlpaal_type = self.filetype_detector.detect(filename)
            if filetype == File.Type.UNKNOWN:
                mijlpaal_type = new_dir.mijlpaal_type
                if mijlpaal_type == MijlpaalType.AANVRAAG:
                    if Path(filename).suffix == '.pdf':
                        filetype = File.Type.AANVRAAG_PDF
                    else:
                        filetype = File.Type.AANVRAAG_OTHER 
                else:
                    filetype = mijlpaal_type.default_filetype()
            log_debug(f'collected: {filetype} {mijlpaal_type}')
            new_dir.register_file(filename=filename, filetype=filetype, mijlpaal_type=mijlpaal_type)
            log_debug('registered')
    def _process_subdirectory(self, subdirectory: str, student: Student)->MijlpaalDirectory:
        if not (parsed := self.parser.parsed(subdirectory)):
            log_warning(f'Onverwachte directory ({Path(subdirectory).stem})')
            return None
        if not (mijlpaal_type := self._parse_type(subdirectory, parsed.type)):
            log_warning(f'\tDirectory {File.display_file(subdirectory)} wordt overgeslagen. Kan niet worden herkend.')
            return None
        new_dir = MijlpaalDirectory(mijlpaal_type=mijlpaal_type, directory=subdirectory, datum=parsed.datum)
        log_debug(f'\tGedetecteerd: {new_dir}')
        self._collect_files(new_dir)
        log_debug('ready detecting')
        return new_dir
    def __update_kansen(self, student_directory: StudentDirectory):
        cur_type = MijlpaalType.UNKNOWN
        cur_kans = 1
        for mijlpaal_directory in sorted(student_directory.directories, key=lambda v: (v.mijlpaal_type, v.datum)):
            if mijlpaal_directory.mijlpaal_type == cur_type:
                cur_kans += 1
            else:
                cur_kans = 1
                cur_type = mijlpaal_directory.mijlpaal_type
            mijlpaal_directory.kans = cur_kans
    def report_directory(self, msg: str, student_directory: StudentDirectory):
        log_print(msg)
        for directory in student_directory.directories:
            log_print(f'\t{str(directory)}')
    def is_new_student(self, student: Student)->bool:
        return student in self.new_students.values()
    def process_file(self, dirname: str, storage: AAPAStorage = None, preview=False)->StudentDirectory:
        if not test_directory_exists(dirname):
            log_error(f'Directory {dirname} niet gevonden.')
            return None
        log_print(f'Verwerken {File.display_file(dirname)}')
        if not self._get_basedir(dirname, storage):
            log_error(f'Directory {File.display_file(dirname)} kan niet worden gelinkt met bekende basisdirectory.')
            return None
        try:    
            student = self._get_student(dirname, storage)
            log_print(f'Student: {student}')
            if self.is_new_student(student):
                log_warning(f'Student {student} nog niet in database. Wordt toegevoegd.\n\tLET OP: controleer het berekende email-adres {student.email} en voeg het juiste studentnummer toe.')
            elif not student.valid():
                log_warning(f'Gegevens student {student} zijn niet compleet.')
            student_directory = StudentDirectory(student, dirname, self.base_dir)
            new_dir = MijlpaalDirectory(mijlpaal_type=MijlpaalType.AANVRAAG, directory=dirname, datum=TSC.AUTOTIMESTAMP)
            self._collect_files(new_dir)
            if new_dir.nr_files() > 0:
                student_directory.add(new_dir)
            # if (aanvraag := self._get_aanvraag(student, storage)):
            #     student_directory.add(aanvraag)
            for subdirectory in Path(dirname).glob('*'):
                if subdirectory.is_dir() and (new_item := self._process_subdirectory(subdirectory, student)):                    
                    student_directory.add(new_item)
            self.__update_kansen(student_directory)
            self.report_directory('Student directory:', student_directory)
            return student_directory
        except DetectorException as reader_exception:
            log_warning(f'{reader_exception}\n\t{StudentDirectoryDetector.ERRCOMMENT}.')
        return None
    
class MilestoneDetectorPipeline(FilePipeline):
    def __init__(self, description: str, storage: AAPAStorage, skip_directories:list[str]=[]):
        super().__init__(description, StudentDirectoryDetector(), storage, activity=UndoLog.Action.DETECT, processing_mode=AAPAProcessingOptions.PROCESSINGMODE.NONE)
        self._processor:StudentDirectoryDetector = self.processors[0]
        self.skip_directories=skip_directories
        self.sqls = self.__init_sql_collectors()
    def __init_sql_collectors(self)->SQLcollectors:
        sqls = SQLcollectors()
        sqls.add('studenten', 
                 SQLcollector(
                {'insert':{'sql':'insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)'},
                }))
        sqls.add('student_directories', 
                 SQLcollector(
                {'insert':{'sql':'insert into STUDENT_DIRECTORIES (id,stud_id,directory,basedir_id) values(?,?,?,?)'},
                'update':{'sql':'update STUDENT_DIRECTORIES set stud_id=?,directory=?,basedir_id=? WHERE id = ?'}}))
        sqls.add('mijlpaal_directories', 
                 SQLcollector
                 ({'insert':{'sql':'insert into MIJLPAAL_DIRECTORIES (id,mijlpaal_type,directory,datum) values(?,?,?,?)'},
                   'update':{'sql':'update MIJLPAAL_DIRECTORIES set mijlpaal_type=?,directory=?,datum=? WHERE id = ?'}}))
        sqls.add('student_directory_directories', SQLcollector(
            {'insert': {'sql':'insert into STUDENT_DIRECTORY_DIRECTORIES (stud_dir_id,mp_dir_id) values(?,?)'},
             'delete': {'sql':'delete from STUDENT_DIRECTORY_DIRECTORIES where stud_dir_id in (?)'}}))
        sqls.add('files', SQLcollector(
             {'insert': {'sql':'insert into FILES (id,filename,timestamp,digest,filetype,mijlpaal_type) values(?,?,?,?,?,?)'},
              'update': {'sql':'update FILES set filename=?,timestamp=?,digest=?,filetype=?,mijlpaal_type=? WHERE id = ?'}}))
        sqls.add('mijlpaal_directory_files', SQLcollector(
            {'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES (mp_dir_id,file_id) values(?,?)',
             'delete': {'sql':'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id=?'}}}))
        return sqls
    @staticmethod
    def __get_values(values: list[Any], id: int, id_first = True)->list[Any]:
        if id_first:
            values.insert(0,id)
        else:
            values.append(id)
        return values
    def __get_sql_mijlpaal_directories(self, stud_dir_id: int, mijlpaal_directory_list: list[MijlpaalDirectory], 
                                       stored_mijlpaal_directories: list[MijlpaalDirectory], stored_files: list[File]):
        def _get_stored(mijlpaal: MijlpaalDirectory, stored_mijlpaal_directories: list[MijlpaalDirectory])->MijlpaalDirectory:
            for stored in stored_mijlpaal_directories:
                if mijlpaal.directory == stored.directory:
                    return stored
            return None
        def _get_values(mijlpaal_directory: MijlpaalDirectory, id_first = True)->list[Any]:
            return self.__get_values([mijlpaal_directory.mijlpaal_type, 
                     Roots.encode_path(mijlpaal_directory.directory), 
                     TSC.timestamp_to_sortable_str(mijlpaal_directory.datum)], mijlpaal_directory.id, id_first)
        self.sqls.delete('student_directory_directories', [stud_dir_id])
        for mijlpaal_directory in mijlpaal_directory_list:
            if stored := _get_stored(mijlpaal_directory, stored_mijlpaal_directories):
                if stored != mijlpaal_directory:
                    self.sqls.update('mijlpaal_directories', _get_values(mijlpaal_directory, False))
            else:
                self.sqls.insert('mijlpaal_directories', _get_values(mijlpaal_directory, True))
            self.sqls.insert('student_directory_directories', [stud_dir_id, mijlpaal_directory.id])
            self.__get_sql_files(mijlpaal_directory.id, mijlpaal_directory.files_list, stored_files=stored_files) 
    def __get_sql_files(self, mp_dir_id: int, files_list: list[File], stored_files: list[File]):
        def _get_values(file: File, id_first = True)->list[Any]:
            return self.__get_values([Roots.encode_path(file.filename),TSC.timestamp_to_sortable_str(file.timestamp),
                                        file.digest,file.filetype,file.mijlpaal_type],
                                      file.id, id_first)
        def _get_stored(file: File, stored_files: list[File])->File:
            for stored in stored_files:
                if file.filename == stored.filename and file.digest == stored.digest:
                    return stored
            return None
        self.sqls.delete('mijlpaal_directory_files', [mp_dir_id])
        for file in files_list:            
            if (stored := _get_stored(file, stored_files)):
                if file != stored: 
                    self.sqls.update('files', _get_values(file, False))                  
            else:
                self.sqls.insert('files', _get_values(file, True))
            self.sqls.insert('mijlpaal_directory_files', [mp_dir_id, file.id])   
    def __get_sql(self, student_directory: StudentDirectory, 
                  stored_directory: StudentDirectory,
                  stored_mijlpaal_directories: list[MijlpaalDirectory], 
                  stored_files: list[File]):         
        def _get_values(student_directory: StudentDirectory, id_first=True):
            return self.__get_values([student_directory.student.id, Roots.encode_path(student_directory.directory), student_directory.base_dir.id], student_directory.id, id_first)
        if stored_directory:
            if stored_directory != student_directory:
                self.sqls.update('student_directories', _get_values(student_directory, False))
        else:
            self.sqls.insert('student_directories', _get_values(student_directory, True))            
        self.__get_sql_mijlpaal_directories(student_directory.id, student_directory.directories, 
                                            stored_mijlpaal_directories=stored_mijlpaal_directories, stored_files=stored_files)
    def __get_stored_files(self, student_directory: StudentDirectory)->list[File]:
        stored_list = []
        for mijlpaal_directory in student_directory.directories:
            files_list = mijlpaal_directory.files_list
            stored_list.extend(self.storage.find_values('files', ['filename', 'digest'], 
                                                    [{file.filename for file in files_list},
                                                     {file.digest for file in files_list}],
                                                     read_many=True))
        return stored_list
    def __get_stored_mijlpaal_directories(self, student_directory: StudentDirectory)->list[MijlpaalDirectory]:       
        result = []
        for mijlpaal in student_directory.directories:
            if stored := self.storage.find_values('mijlpaal_directories', 'directory', Roots.encode_path(mijlpaal.directory)):
                result.append(stored[0])
        return result
    def _store_new(self, student_directory: StudentDirectory):
        if stored := self.storage.find_values('student_directories', 'directory', Roots.encode_path(student_directory.directory)):
            stored_directory = stored[0]
        else:
            stored_directory = None
        stored_files = self.__get_stored_files(student_directory)
        stored_mijlpaal_directories = self.__get_stored_mijlpaal_directories(student_directory)

        self.storage.create('student_directories', student_directory)

        #must get the right IDs from the database first to get the correct SQL codes
        self.__get_sql(self.storage.read('student_directories', student_directory.id), stored_directory, stored_mijlpaal_directories, stored_files)
        student_id = student_directory.student.id
        log_debug(f'inserting new students {[id for id in self._processor.new_students.keys()]}')
        if student_id in self._processor.new_students.keys():
            student = self._processor.new_students[student_id]
            log_debug(f'\tinserting {student}')
            self.sqls.insert('studenten', [student.id,StudentDirectoryDetector.UNKNOWN_STUDNR,student.full_name,student.first_name,student.email,student.status])
    def _skip(self, filename: str)->bool:        
        if Path(filename).stem in self.skip_directories:
            return True
        return False

class DirectoryDetectorPlugin(PluginBase):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--directory', dest='directory', type=str,help=r'Detecteer gegevens vanuit een directory bv: --directory=c:\users\david\NHL Stenden\...')
        parser.add_argument('--json', dest='json', type=str,help='JSON filename waar SQL output wordt weggeschreven\nDefault: samengesteld uit de naam van de detect-diretory') 
        return parser
    
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        self.json_filename = kwdargs.get('json_filename', None)
        directory = Roots.decode_path(kwdargs.get('directory', ''))
        if not Path(directory).is_dir():
            log_error(f'Map {directory} bestaat niet. Afbreken.')
            return False
        self.directory = directory        
        context.processing_options.debug = True
        context.processing_options.preview = True
        self.storage = context.storage
        log_info(f'Start detectie van map  {directory}...', to_console=True)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        self.importer = MilestoneDetectorPipeline(f'Detectie studentgegevens uit directory {self.directory}', self.storage, 
                                             skip_directories=SKIP_DIRECTORIES)
        (n_processed, n_files) = self.importer.process([dir for dir in Path(self.directory).glob('*') if (dir.is_dir() and str(dir).find('.git') ==-1)], preview=context.preview)
        log_info(f'...Detectie afgerond ({sop(n_processed, "directory", "directories", prefix="nieuwe student-")}. In directory: {sop(n_files, "subdirectory", "subdirectories")})', to_console=True)
        return True
    def after_process(self, context: AAPARunnerContext, process_result: bool):
        if not process_result:
            return
        if not self.json_filename:
            json_filename= f'{Path(self.directory).parent.name}_{Path(self.directory).stem}.json'
        self.importer.sqls.dump_to_file(json_filename)
        log_print(f'SQL data dumped to file {json_filename}')