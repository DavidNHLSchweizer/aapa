""" IMPORT_STUDENTEN

    Genereert SQL-code om studenten vanuit een Excel-sheet met kolommen 
        'achternaam', 'voornaam', 'studnr', 'email', 'status' toe te voegen.

    Kan gebruikt worden om studenten die ontbreken in de database
    of incorrecte gegevens hebben te corrigeren.

    De resultaten worden als .json  weggeschreven.

    De gegeneerde SQL-code kan met "run_extra.py json" worden uitgevoerd.

"""
#TODO: testen na overzetten naar Plugin. Heeft geen haast

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Tuple
from typing import Any
from storage.general.mappers import ColumnMapper, ObjectMapper
from data.classes.studenten import Student
from data.classes.undo_logs import UndoLog
from general.sql_coll import SQLcollector, SQLcollectors
from storage.aapa_storage import AAPAStorage
from storage.queries.studenten import StudentQueries
from main.log import init_logging, log_error, log_info, log_print, log_warning
from process.general.preview import Preview, pva
from general.singular_or_plural import sop
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from process.general.base_processor import FileProcessor
from process.general.pipeline import SingleFilePipeline
from process.input.importing.excel_reader import ExcelReader

class StudentExcelMapper(ObjectMapper):
    COLUMNS =  ['achternaam', 'voornaam', 'studnr', 'email', 'status']
    def __init__(self):
        super().__init__(self.COLUMNS, Student)
    @staticmethod
    def status_db_to_value(value: str)->Student.Status:
        STATUS_CODES = {'aanvraag': Student.Status.AANVRAAG, 'bezig': Student.Status.BEZIG, 'afgestudeerd': Student.Status.AFGESTUDEERD,'gestopt': Student.Status.GESTOPT,}
        return STATUS_CODES.get(value, Student.Status.UNKNOWN)
    def _init_column_mapper(self, column_name: str) -> ColumnMapper:
        match column_name:
            case 'achternaam': return ColumnMapper(column_name=column_name, attribute_name='last_name')
            case 'voornaam': return ColumnMapper(column_name=column_name, attribute_name='first_name')
            case 'studnr': return ColumnMapper(column_name=column_name, attribute_name='stud_nr')
            case 'status': return ColumnMapper('status', db_to_obj=self.status_db_to_value)
            case _: return super()._init_column_mapper(column_name)

class StudentenXLSImporter(FileProcessor):
    def __init__(self):
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        self.sql=SQLcollectors()# to use in migration script
        self.sql.add('studenten',
            SQLcollector({'insert':{'sql':'insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)'}, 
             'update':{'sql':'update STUDENTEN set full_name=?,first_name=?,email=?,status=? where stud_nr = ?'}}))
        super().__init__(description='Importeren studenten')
    def __add_sql(self, student: Student, is_new=True):
        if is_new:
            self.sql.insert('studenten', [student.id, str(student.stud_nr), student.full_name, student.first_name, student.email, int(student.status)])
        else:
            self.sql.update('studenten', [student.full_name, student.first_name, student.email, int(student.status), str(student.stud_nr)])
    def __check_and_store_student(self, student: Student, storage: AAPAStorage)->Any:
        def check_diff(student: Student, stored: Student, attrib: str)->bool:
            a1 = str(getattr(student, attrib, None))
            a2 = str(getattr(stored, attrib, None))
            if  a1 != a2:
                log_warning(f'\tVerschil in {attrib}: {a1}, {a2} in database.')
                return True
            return False
        queries: StudentQueries = storage.queries('studenten')
        if stored:=queries.find_student_by_name_or_email_or_studnr(student):
            log_warning(f'\tStudent {student} al in database')
            different = check_diff(student, stored, 'email') or\
                    check_diff(student, stored, 'first_name') or\
                    check_diff(student, stored, 'stud_nr') or\
                    check_diff(student, stored, 'status')
            if different:
                self.n_modified += 1
                storage.update('studenten', student)
                self.__add_sql(student, False)
            else:
                self.n_already_there += 1
        else:
            log_info(f'\tNieuwe student: {student}', to_console=True)
            storage.create('studenten', student)
            self.__add_sql(student, True)
            self.n_new += 1
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Tuple[int,int,int]:
        reader = ExcelReader(filename, StudentExcelMapper.COLUMNS)
        if reader.error:
            log_error(f'Kan studentgegevens niet importeren uit {filename}.\n\t\
                      {reader.error}.')
            return 0
        mapper = StudentExcelMapper()
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        for row,value in enumerate(reader.read()):
            if not (student := mapper.db_to_object(value)):
                log_error(f'Fout bij lezen rij {row}: {value}.')
            else:
                self.__check_and_store_student(student, storage)
        return (self.n_new,self.n_modified,self.n_already_there)
                    
class StudentenExcelImporter(PluginBase):
    def get_parser(self) -> ArgumentParser:
        parser.add_argument('--json', dest='json', required=True, type=str,help='JSON filename waar SQL output wordt weggeschreven') 
        parser.add_argument('--student', dest='student', required=True, type=str,help='Importeer gegevens over studenten uit Excel-bestand') 
        parser = super().get_parser()
        return parser
    
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        context.processing_options.debug = True
        context.processing_options.preview = True
        self.json_filename=kwdargs.get('json', '')
        self.xls_filename = kwdargs.get('student') 
        self.storage = context.configuration.storage
        self.importer = StudentenXLSImporter()
        self.pipeline = SingleFilePipeline('Importeren studenten uit XLS bestand', self.importer, 
                                  self.storage, activity=UndoLog.Action.NOLOG)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        with Preview(context.preview,self.storage, 'Importeren studenten'):
            (n_new,n_modified,n_already_there)=self.pipeline.process(self.xls_filename, preview=context.preview)
            if n_new == 0:
                log_print(f'Geen nieuwe studenten om te importeren ({n_already_there} al in database, {n_modified} aangepast met nieuwe gegevens).')
            else:
                log_print(f'{sop(n_new, "student", "studenten", prefix="nieuwe ")} {pva(context.preview, "te importeren", "geimporteerd")} uit {self.xls_filename}.')
                log_print(f'{sop(n_modified, "student", "studenten")} {pva(self.preview, "aan te passen", "aangepast")} volgens {self.xls_filename}.')
                log_print(f'{sop(n_already_there, "student", "studenten")} al in database.')
                log_print(f'{sop(n_new+n_modified, "student", "studenten")} {pva(self.preview, "te importeren of aan te passen", "geimporteerd of aangepast")} volgens {self.xls_filename}.')
        return True
    def after_process(self, context: AAPARunnerContext, process_result: bool):
        if not process_result:
            return False
        self.importer.sql.dump_to_file(self.json_filename)
        log_print(f'SQL data dumped to file {self.json_filename}')
