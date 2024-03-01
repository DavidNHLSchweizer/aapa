""" CORRECT_MP_DIRS. 

    aanpassen van database voor dubbelingen in mijlpaal_directories voor files (verslagen).
    
    bedoeld voor migratie db naar versie 1.24
    
"""
from pathlib import Path
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.roots import Roots
from storage.queries.student_directories import StudentDirectoriesQueries
from general.sql_coll import SQLcollector, SQLcollectors
from general.timeutil import TSC
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext


class MijlpaalDirsReEngineeringProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('student_directory_directories', SQLcollector({'delete': {'sql': 'delete from STUDENT_DIRECTORY_DIRECTORIES where mp_dir_id in (?)'},}))
        sql.add('mijlpaal_directory_files', SQLcollector({'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES(mp_dir_id,file_id) values(?,?)'},
                                                               'delete': {'sql': 'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id in (?)'},}))
        sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set mijlpaal_type=?,kans=?,directory=?,datum=? where id=?'},
                                                           'delete': {'sql': 'delete from MIJLPAAL_DIRECTORIES where id in (?)'},}))
        return sql
    def _sql_delete_mijlpaal_directory_files(self, mp_dir: MijlpaalDirectory):
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
    def _sql_delete_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        self._sql_delete_mijlpaal_directory_files(mp_dir)
        self.sql.delete('student_directory_directories', [mp_dir.id])
        self.sql.delete('mijlpaal_directories', [mp_dir.id])
    def _sql_update_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
        self.sql.update('mijlpaal_directories', [mp_dir.mijlpaal_type,mp_dir.kans,
                                                 Roots.encode_path (mp_dir.directory), TSC.timestamp_to_sortable_str(mp_dir.datum), mp_dir.id])
    def _correct_directory(self, mp_dir_list: list[MijlpaalDirectory]):
        first_mp_dir = mp_dir_list[0] # the list was sorted on id`
        self._sql_delete_mijlpaal_directory_files(first_mp_dir)
        for mp_dir in mp_dir_list[1:]:
            for file in mp_dir.files.files:
                first_mp_dir.files.add(file)
            self._sql_delete_mijlpaal_directory(mp_dir)
            mp_dir.files.clear('files')
        self._sql_update_mijlpaal_directory(first_mp_dir)
    def process_double_entry(self, directory: str, ids: list[int]):
        mp_dirs = self.storage.read_many('mijlpaal_directories', set(ids))
        print(f'correcting {File.display_file(directory)}: ({ids})')
        self._correct_directory(mp_dirs)
    def _get_double_entries(self)->dict:
        query = 'select id,directory from MIJLPAAL_DIRECTORIES as MPD1 where exists (select id from MIJLPAAL_DIRECTORIES as MPD2 where MPD1.id <> MPD2.id and MPD1.directory = MPD2.directory) order by 2,1'
        rows = self.database._execute_sql_command(query,[], True)
        cur_directory = None
        cur_ids = []
        double_entries = {}
        for row in rows:
            id = row['id']
            directory = row['directory']
            if not cur_directory:
                cur_directory = directory
            elif directory!=cur_directory:
                double_entries[cur_directory] = cur_ids.copy()
                cur_directory = directory
                cur_ids = []
            cur_ids.append(id)
        if cur_ids:
            double_entries[cur_directory] = cur_ids
        return double_entries
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        def dump_info(msg: str, dir_list:list[MijlpaalDirectory]):
            self.log(f'\t--- {msg} ---')
            for dir in dir_list:
                filestr = "\n\t\t".join([Path(file.filename).name for file in dir.files_list]) if dir.files_list else '<No files>'
                self.log(f'\t{dir.id}-{dir.datum}: {File.display_file(dir.directory)}\n\t\t{filestr}')
        double_entries = self._get_double_entries()
        for directory, ids in double_entries.items():
            self.process_double_entry(directory, ids)
        return True
