from __future__ import annotations
from argparse import ArgumentParser
from pathlib import Path
import re
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.general.roots import Roots
from general.singular_or_plural import sop
from general.sql_coll import SQLcollector, SQLcollectors
from main.log import log_error, log_info, log_print
from plugins.plugin import PluginBase
from process.input.importing.dirname_parser import DirectoryNameParser
from process.main.aapa_processor import AAPARunnerContext
from storage.aapa_storage import AAPAStorage
from storage.queries.files import FilesQueries
from storage.queries.studenten import StudentQueries

class OrphanException(Exception): pass

class OrphanFileProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.database = storage.database
        self.file_queries: FilesQueries = self.storage.queries('files')
        self.student_queries: StudentQueries = self.storage.queries('studenten')
        self.skip_pattern2023 = re.compile(r"Beoordeling aanvragen 2023\\Week\s\d")
        self.skip_pattern2024 = re.compile(r"0_Beoordeling aanvragen 2024\\Week\s\d")
        self.parser = DirectoryNameParser()
        self.sql = self._init_sql()
    def _init_sql(self):
        sql = SQLcollectors()
        sql.add('mijlpaal_directory_files', SQLcollector(
            {'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES (mp_dir_id,file_id) values(?,?)',}}))
        return sql
    def _get_student(self,filename: str)->Student:
        if not (parsed := self.parser.parsed(Path(filename).parent)):
            raise OrphanException(f'directory {File.display_file(filename)} kan niet worden geanalyseerd.')
        tem_student = Student(full_name=parsed.student,email=parsed.email())
        if not (stored := self.student_queries.find_student_by_name_or_email_or_studnr(tem_student)):
            raise OrphanException(f'Student kan niet worden gevonden voor wees-file {File.display_file(filename)}')
        return stored
    def _get_mijlpaal_dir(self, filename: str)->MijlpaalDirectory:
        if (rows:=self.storage.queries('mijlpaal_directories').find_values('directory', Roots.encode_path(Path(filename).parent))):
            return rows[0]
        return None
    def _is_in_beoordeling_aanvraag_directory(self, filename: str)->bool:
        return self.skip_pattern2023.search(filename) is not None or self.skip_pattern2024.search(filename)
    def _add_to_mijlpaal(self, mijlpaal_dir: MijlpaalDirectory, file: File):
        mijlpaal_dir.files.add(file)
        self.sql.insert('mijlpaal_directory_files', [mijlpaal_dir.id, file.id])
    def handle_file(self, file: File)->bool:
        if self._is_in_beoordeling_aanvraag_directory(file.filename):
            return True
        try:
            student = self._get_student(file.filename)
            if student.status in {Student.Status.AFGESTUDEERD,Student.Status.GESTOPT}:
                return True
            mijlpaal_dir = self._get_mijlpaal_dir(file.filename)
            if not mijlpaal_dir: 
                raise OrphanException(f'Cannot find MijlpaalDirectory for {file.filename}')
            if mijlpaal_dir.mijlpaal_type != file.mijlpaal_type:
                raise OrphanException(f'Incompatible mijlpaaltypes... {mijlpaal_dir.mijlpaal_type}, {file.mijlpaal_type}')
            self._add_to_mijlpaal(mijlpaal_dir, file)            
            return True
        except OrphanException as E:
            log_error(f'Bestand {File.display_file(file.filename)} kan niet aan student worden gekoppeld.')    
            return False
        
    def process(self, preview=False, sql: SQLcollectors = None)->bool:
        old_sql = self.sql
        if sql is not None:
            self.sql = sql
        n_handled = 0
        query = f'select id from FILES as F where not exists (select * from MIJLPAAL_DIRECTORY_FILES where file_id = F.id) and not F.filetype in (?,?,?,?,?)'        
        if rows:=self.database._execute_sql_command(query, [File.Type.INVALID_DOCX, File.Type.INVALID_PDF, File.Type.COPIED_PDF,File.Type.DIFFERENCE_HTML, File.Type.GRADE_FORM_DOCX], True):
            orphan_files = list(filter(lambda f: Roots.is_on_onedrive(f.filename), self.storage.read_many('files', {row['id'] for row in rows})))
        else:
            orphan_files = []
        for orphan in orphan_files:
            if self.handle_file(orphan):
                n_handled +=1
        self.sql = old_sql
        log_print(f'{sop(n_handled, 'wees', 'wezen')} vastgeplakt.')
        return n_handled > 0

class OrphanFilesPlugin(PluginBase):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--json', dest='json', type=str,help='JSON filename waar SQL output wordt weggeschreven') 
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.processor = OrphanFileProcessor(context.configuration.storage)
        self.json = kwdargs.get('json')
        if not self.json:
            self.json = 'orphan_files.json'
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        print('Start running orphan-files')
        self.processor.process(context.preview)
        self.processor.sql.dump_to_file(self.json)
        print(f'sql dumped to {self.json}')
