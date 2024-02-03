from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Tuple
from typing import Any

from data.classes.base_dirs import BaseDir
from data.classes.mappers import ColumnMapper, FilenameColumnMapper, ObjectMapper
from data.classes.undo_logs import UndoLog
from general.sql_coll import SQLcollector, SQLcollectors
from data.roots import add_root, encode_path
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.base_dirs import BaseDirQueries
from general.log import init_logging, log_error, log_info, log_print, log_warning
from general.preview import Preview, pva
from general.singular_or_plural import sop
from process.aapa_processor.aapa_processor import AAPARunnerContext
from process.general.base_processor import FileProcessor
from process.general.pipeline import SingleFilePipeline
from process.input.importing.excel_reader import ExcelReader

EXTRA_DOC = """

    IMPORT_BASEDIRS

    Genereert SQL-code om basedirs vanuit een Excel-sheet met kolommen 
        'jaar', 'periode', 'forms_versie', 'directory' toe te voegen.

    Kan gebruikt worden om nieuwe base directories toe te voegen aan de database.

    De resultaten worden als .json  weggeschreven.

    De gegeneerde SQL-code kan met "run_extra.py json" worden uitgevoerd.

"""

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
            root_code = add_root(base_dir.directory)            
            self.sql.insert('fileroot', [root_code, base_dir.directory])
            self.sql.insert('base_dirs', [base_dir.id, base_dir.year, base_dir.period, base_dir.forms_version, root_code])
        else:
            self.sql.update('base_dirs', [base_dir.year,base_dir.period, base_dir.forms_version, encode_path(base_dir.directory), base_dir.stud_nr])
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
        
def import_basedirs_XLS(xls_filename: str, storage: AAPAStorage, json_filename: str = "insert_basedirs.json", preview=True):
    importer = BasedirXLSImporter()
    pipeline = SingleFilePipeline('Importeren basedirs uit XLS bestand', importer, 
                                  storage, activity=UndoLog.Action.NOLOG)
    with Preview(preview,storage, 'Importeren basedirs'):
        (n_new,n_modified,n_already_there)=pipeline.process(xls_filename, preview=preview)
        if n_new == 0:
            log_print(f'Geen nieuwe basedirs om te importeren ({n_already_there} al in database, {n_modified} aangepast met nieuwe gegevens).')
        else:
            log_print(f'{sop(n_new, "base_dir", "basedirs", prefix="nieuwe ")} {pva(preview, "te importeren", "geimporteerd")} uit {xls_filename}.')
            log_print(f'{sop(n_modified, "base_dir", "basedirs")} {pva(preview, "aan te passen", "aangepast")} volgens {xls_filename}.')
            log_print(f'{sop(n_already_there, "base_dir", "basedirs")} al in database.')
            log_print(f'{sop(n_new+n_modified, "base_dir", "basedirs")} {pva(preview, "te importeren of aan te passen", "geimporteerd of aangepast")} volgens {xls_filename}.')
            importer.sql.dump_to_file(json_filename)
            log_print(f'SQL data dumped to file {json_filename}')

def prog_parser(base_parser: ArgumentParser)->ArgumentParser:
    base_parser.add_argument('--json', dest='json', required=True, type=str,help='JSON filename waar SQL output wordt weggeschreven') 
    base_parser.add_argument('--basedir', dest='basedir', required=True, type=str,help='Importeer gegevens over basedirs uit Excel-bestand') 
    return base_parser

def extra_action(context:AAPARunnerContext, namespace: Namespace):
    context.processing_options.debug = True
    context.processing_options.preview = True
    init_logging('import_basedirs.log', True)
    json_filename=namespace.json 
    xls_filename = namespace.basedir 
    with context:        
        storage = context.configuration.storage
        with Preview(True,storage,'Maak extra aanvragen (voor migratie)'):
            import_basedirs_XLS(xls_filename,storage, json_filename=json_filename, preview=True)