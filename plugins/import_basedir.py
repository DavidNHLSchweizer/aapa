""" IMPORT_BASEDIRS

    Genereert SQL-code om basedirs vanuit een Excel-sheet met kolommen 
        'jaar', 'periode', 'forms_versie', 'directory' toe te voegen.

    Kan gebruikt worden om nieuwe base directories toe te voegen aan de database.

    De resultaten worden als .json  weggeschreven.

    De gegeneerde SQL-code kan met "run_extra.py json" worden uitgevoerd.
"""
#TODO: testen na overzetten naar Plugin. Heeft geen haast
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Tuple
from typing import Any

from data.classes.base_dirs import BaseDir
from storage.general.mappers import ColumnMapper, FilenameColumnMapper, ObjectMapper
from data.classes.undo_logs import UndoLog
from general.sql_coll import SQLcollector, SQLcollectors
from data.general.roots import Roots
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirQueries
from main.log import init_logging, log_error, log_info, log_print, log_warning
from process.general.preview import Preview, pva
from general.singular_or_plural import sop
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from process.general.base_processor import FileProcessor
from process.general.pipeline import SingleFilePipeline
from process.input.importing.excel_reader import ExcelReader


class BaseDirExcelMapper(ObjectMapper):
    COLUMNS =  ['jaar', 'periode', 'forms_versie', 'directory']
    def __init__(self):
        super().__init__(self.COLUMNS, BaseDir)
    def _init_column_mapper(self, column_name: str) -> ColumnMapper:
        match column_name:
            case 'jaar': return ColumnMapper(column_name=column_name, attribute_name='year')
            case 'periode': return ColumnMapper(column_name=column_name, attribute_name='period')
            case 'forms_versie': return ColumnMapper(column_name=column_name, attribute_name='forms_version')
            case 'directory': return FilenameColumnMapper(column_name)
            case _: return super()._init_column_mapper(column_name)

class BasedirXLSImporter(FileProcessor):
    def __init__(self):
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        self.sql=SQLcollectors()# to use in migration script
        self.sql.add('base_dirs',
            SQLcollector({'insert':{'sql':'insert into BASEDIRS (id,year,period,forms_version,directory) values(?,?,?,?,?)'}, 
             'update':{'sql':'update BASEDIRS set year=?,period=?,forms_version=?,directory=? where id = ?'}}))
        self.sql.add('fileroot', SQLcollector({'insert':{'sql':'insert into FILEROOT (code,root) values(?,?)'}, })) 
        super().__init__(description='Importeren basedirs')
    def __add_sql(self, base_dir: BaseDir, is_new=True):
        if is_new:
            root_code = Roots.add_root(base_dir.directory)            
            self.sql.insert('fileroot', [root_code, base_dir.directory])
            self.sql.insert('base_dirs', [base_dir.id, base_dir.year, base_dir.period, base_dir.forms_version, root_code])
        else:
            self.sql.update('base_dirs', [base_dir.year,base_dir.period, base_dir.forms_version, Roots.encode_path(base_dir.directory), base_dir.stud_nr])
    def __check_and_store_basedir(self, base_dir: BaseDir, storage: AAPAStorage)->Any:
        def check_diff(base_dir: BaseDir, stored: BaseDir, attrib: str)->bool:
            a1 = str(getattr(base_dir, attrib, None))
            a2 = str(getattr(stored, attrib, None))
            if  a1 != a2:
                log_warning(f'\tVerschil in {attrib}: {a1}, {a2} in database.')
                return True
            return False
        queries: BaseDirQueries  = storage.queries('base_dirs')
        if rows:=queries.find_values(['year', 'period', 'forms_version'], [base_dir.year, base_dir.period, base_dir.forms_version], map_values=False):
            stored = rows[0]
            log_warning(f'\tBasedir {base_dir} al in database')
            different = check_diff(base_dir, stored, 'year') or\
                    check_diff(base_dir, stored, 'period') or\
                    check_diff(base_dir, stored, 'forms_version') or\
                    check_diff(base_dir, stored, 'directory')
            if different:
                self.n_modified += 1
                storage.update('base_dirs', base_dir)
                self.__add_sql(base_dir, False)
            else:
                self.n_already_there += 1
        else:
            log_info(f'\tNieuwe base_dir: {base_dir}', to_console=True)
            storage.create('base_dirs', base_dir)
            self.__add_sql(base_dir, True)
            self.n_new += 1
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Tuple[int,int,int]:
        reader = ExcelReader(filename, BaseDirExcelMapper.COLUMNS)
        if reader.error:
            log_error(f'Kan basedir-gegevens niet importeren uit {filename}.\n\t\
                      {reader.error}.')
            return 0
        mapper = BaseDirExcelMapper()
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        for row,value in enumerate(reader.read()):
            if not (base_dir := mapper.db_to_object(value)):
                log_error(f'Fout bij lezen rij {row}: {value}.')
            else:
                self.__check_and_store_basedir(base_dir, storage)
        return (self.n_new,self.n_modified,self.n_already_there)

class BaseDirsExcelImporter(PluginBase):
    def get_parser(self) -> ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--json', dest='json', required=True, type=str,help='JSON filename waar SQL output wordt weggeschreven') 
        parser.add_argument('--basedir', dest='basedir', required=True, type=str,help='Importeer gegevens over basedirs uit Excel-bestand') 
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        context.processing_options.debug = True
        context.processing_options.preview = True
        self.json_filename=kwdargs.get('json', '')
        self.xls_filename = kwdargs.get('basedir') 
        self.storage = context.configuration.storage
        self.importer = BasedirXLSImporter()
        self.pipeline = SingleFilePipeline('Importeren basedirs uit XLS bestand', self.importer, 
                                  self.storage, activity=UndoLog.Action.NOLOG)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        with Preview(context.preview):
            (n_new,n_modified,n_already_there)=self.pipeline.process(self.xls_filename, preview=context.preview)
            if n_new == 0:
                log_print(f'Geen nieuwe basedirs om te importeren ({n_already_there} al in database, {n_modified} aangepast met nieuwe gegevens).')
            else:
                log_print(f'{sop(n_new, "base_dir", "basedirs", prefix="nieuwe ")} {pva(context.preview, "te importeren", "geimporteerd")} uit {self.xls_filename}.')
                log_print(f'{sop(n_modified, "base_dir", "basedirs")} {pva(context.preview, "aan te passen", "aangepast")} volgens {self.xls_filename}.')
                log_print(f'{sop(n_already_there, "base_dir", "basedirs")} al in database.')
                log_print(f'{sop(n_new+n_modified, "base_dir", "basedirs")} {pva(context.preview, "te importeren of aan te passen", "geimporteerd of aangepast")} volgens {self.xls_filename}.')
        return True
    def after_process(self, context: AAPARunnerContext, process_result: bool):
        if not process_result:
            return False
        self.importer.sql.dump_to_file(self.json_filename)
        log_print(f'SQL data dumped to file {self.json_filename}')
