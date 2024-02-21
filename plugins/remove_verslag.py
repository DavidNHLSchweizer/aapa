""" REMOVE_VERSLAG.

    Verwijdert 1 of meer verslagen uit de database.
    Alle gerelateerde records worden ook verwijderd.

"""
from argparse import ArgumentParser
from pathlib import Path
import shutil
import tkinter
from tkinter.messagebox import askokcancel, askyesno
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.verslagen import Verslag
from main.log import log_error, log_print
from general.sql_coll import SQLcollector, SQLcollectors
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from storage.queries.student_directories import StudentDirectoryQueries
from main.config import config

class RemoverException(Exception):pass

class VerslagRemover(PluginBase):
    def init_sql(self)->SQLcollectors:
        sql = SQLcollectors()
        sql.add('undologs_verslagen',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_VERSLAGEN where verslag_id in (?)'},}))
        sql.add('undologs_files',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_FILES where file_id in (?)'},}))
        sql.add('verslagen_files', SQLcollector({'delete':{'sql':'delete from VERSLAGEN_FILES where verslag_id in (?)'}, }))
        sql.add('verslagen', SQLcollector({'delete':{'sql':'delete from VERSLAGEN where id in (?)'}, }))
        sql.add('mijlpaal_directory_files', SQLcollector({'delete':{'sql':'delete from MIJLPAAL_DIRECTORY_FILES where file_id in (?)'}, }))
        sql.add('mijlpaal_directories', SQLcollector({'delete':{'sql':'delete from MIJLPAAL_DIRECTORIES where id in (?)'}, }))
        sql.add('student_directory_directories', SQLcollector({'delete':{'sql':'delete from STUDENT_DIRECTORY_DIRECTORIES where mp_dir_id in (?)'}, }))
        sql.add('files', SQLcollector({'delete':{'sql':'delete from FILES where id in (?)'}, }))                 
        return sql
    def _find_mp_dir(self, verslag: Verslag)->MijlpaalDirectory:
        target_dir = verslag.get_directory()
        for mp_dir in self.stud_dir_queries.find_student_mijlpaal_dir(verslag.student, verslag.mijlpaal_type):
            if str(mp_dir.directory) == target_dir:
                return mp_dir
        return None
    def _unlink_files(self, verslag: Verslag, preview: bool):
        mp_dir = self._find_mp_dir(verslag)
        if not mp_dir:
            log_print(f'Kan mijlpaaldirectory voor verslag {verslag.summary()} niet vinden.')
            return
        if str(mp_dir.directory).lower() in self.removed_directories:
            return
        log_print(f'Verwijderen: {File.display_file(mp_dir.directory)}')
        if not preview:
            try:
                shutil.rmtree(mp_dir.directory)
                self.removed_directories.add(str(mp_dir.directory).lower())
            except Exception as E:
                log_print(f'Fout bij verwijderen {File.display_file(mp_dir.directory)}:\n\t{E}')            
        for file in mp_dir.files_list:
            self.sql.delete('undologs_files', [file.id])
            self.sql.delete('files', [file.id])
            self.sql.delete('mijlpaal_directory_files', [file.id])
        self.sql.delete('mijlpaal_directories', [mp_dir.id])
        self.sql.delete('student_directory_directories', [mp_dir.id])            
    def _remove_verslag(self, verslag: Verslag):
        self.sql.delete('undologs_verslagen', [verslag.id])
        self.sql.delete('verslagen_files', [verslag.id])
        for file in verslag.files_list:
            self.sql.delete('undologs_files', [file.id])
            self.sql.delete('files', [file.id])
            self.sql.delete('mijlpaal_directory_files', [file.id])
        self.sql.delete('verslagen', [verslag.id])
    def remove(self, verslag_id: int|list[int], unlink: bool, preview: bool):
        verslagen_ids = verslag_id if isinstance(verslag_id, list) else [verslag_id]
        for id in verslagen_ids:
            if not (verslag := self.storage.read('verslagen', id)):
                log_error(f'Can not read verslag {id}')
                continue
            log_print(f'removing verslag {id}: {verslag.summary()}')
            if unlink:
                self._unlink_files(verslag, preview)
            self._remove_verslag(verslag)
        self.sql.execute_sql(self.storage.database, preview)
        self.storage.commit()
        log_print(f'Removed verslagen {verslagen_ids}.')
    def get_parser(self) -> ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--verslag', type=int, action='append', help='id van verslag(en) om te verwijderen. Kan meerdere malen worden ingevoerd : --verslag=id1 --verslag=id2.')
        parser.add_argument('-unlink', action='store_true', help='verwijder ook alle bestanden uit het filesysteem.')
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        super().before_process(context, **kwdargs)
        self.sql = self.init_sql()
        self.removed_directories = set()
        self.storage=context.storage
        self.stud_dir_queries:StudentDirectoryQueries = self.storage.queries('student_directories')
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        verslagen = kwdargs.get('verslag')
        if not verslagen:
            print('Geen verslagen ingevoerd.')
            return False
        print(f'Verslagen om te verwijderen: {verslagen}')
        unlink = kwdargs.get('unlink', False)
        if unlink and not context.preview:
            fileroot_parts = list(Path(config.get('configuration', 'root')).parts)            
            display  = Path(fileroot_parts[0]).joinpath(*tuple(fileroot_parts[1:4]))
            if not (context.processing_options.force or askokcancel('Zeker weten?', f'Dit verwijdert bestanden van het filesysteem.\nFilesysteem:\n\n{display}\\...\n\nDoe dit nooit zonder zeker te weten dat je dit wilt!\nDoorgaan?')):
                return False
        self.remove(verslagen, unlink, context.preview)
        return True
