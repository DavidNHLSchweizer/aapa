""" ADD_ORPHAN_VERSLAGEN. 

    aanpassen van database voor verslagen zonder files.
    blijft nog 1 inconsistentie over: Nick de Boer     
    Dat laten we maar zo.

    bedoeld voor migratie db naar versie 1.24
    
"""
from pathlib import Path
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.verslagen import Verslag
from data.general.roots import Roots
from main.log import log_error
from storage.queries.files import FilesQueries
from storage.queries.student_directories import StudentDirectoryQueries
from general.sql_coll import SQLcollector, SQLcollectors
from general.timeutil import TSC
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext
from main.config import config


class OrphanVerslagenProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('verslagen', SQLcollector({'delete': {'sql': 'delete from VERSLAGEN where id in (?)'},}))
        sql.add('verslagen_files', SQLcollector({'insert': {'sql':'insert into VERSLAGEN_FILES(verslag_id,file_id) values(?,?)'},}))
        return sql
    def _determine_directory(self, stud_dir: StudentDirectory, verslag: Verslag)->str:
        if directory := verslag.get_directory():
            return directory
        if (mp_dir := stud_dir.get_directory(verslag.datum, verslag.mijlpaal_type, config.get('directories', 'error_margin_date'))):
            return mp_dir.directory
        if (mp_dirs := stud_dir.get_directories(verslag.mijlpaal_type)):
            return mp_dirs[-1].directory
        #try previous stud dir
        for old_stud_dir in sorted(self.student_dir_queries.find_student_dirs(stud_dir.student), key=lambda sd: sd.id, reverse=True):
            if old_stud_dir.id >= stud_dir.id:
                continue
            if dir := self._determine_directory(old_stud_dir, verslag):
                return dir

        return None
    def _process_verslag(self, stud_dir: StudentDirectory, verslag: Verslag):
        directory = self._determine_directory(stud_dir, verslag)        
        if not directory:
            log_error(f'Kan plaats bestanden voor verslag {verslag.summary()} niet vaststellen. Verslag wordt verwijderd, waarschijnlijk inconsistent.')
            self.sql.delete('verslagen', [verslag.id])
            return
        default_filetype = verslag.mijlpaal_type.default_filetype()
        files = list(filter(lambda f: f.filetype == default_filetype, self.files_query.files_in_directory(str(directory))))
        for file in files:
            self.sql.insert('verslagen_files', [verslag.id,file.id])
    def process_orphans(self, stud_id: int, ids: list[int]):
        stud_dir = self.student_dir_queries.find_student_dir(self.storage.read('studenten', stud_id))
        for verslag in self.storage.read_many('verslagen', set(ids)):
            self._process_verslag(stud_dir, verslag)
        # mp_dirs = self.storage.read_many('mijlpaal_directories', set(ids))
        # print(f'correcting {File.display_file(directory)}: ({ids})')
        # self._correct_directory(mp_dirs)
    def _get_orphan_entries(self)->dict:
        query = 'select V.id, V.stud_id from VERSLAGEN as V where not exists (select VF.verslag_id from VERSLAGEN_FILES as VF where VF.verslag_id = V.id) order by 2'
        rows = self.database._execute_sql_command(query,[], True)
        cur_student = None
        cur_ids = []
        orphans = {}
        for row in rows:
            verslag_id = row['id']
            student_id = row['stud_id']
            if not cur_student:
                cur_student = student_id
            elif student_id!=cur_student:
                orphans[cur_student] = cur_ids.copy()
                cur_student = student_id
                cur_ids = []
            cur_ids.append(verslag_id)
        if cur_ids:
            orphans[cur_student] = cur_ids
        return orphans
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        self.files_query: FilesQueries = self.storage.queries('files')
        self.database = context.storage.database
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        orphans = self._get_orphan_entries()        
        for stud_id, ids in orphans.items():
            self.process_orphans(stud_id, ids)
        return True
