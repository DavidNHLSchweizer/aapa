from pathlib import Path
from typing import Tuple
from enum import Enum
from typing import Any

import pandas as pd
from data.classes.base_dirs import BaseDir
from data.classes.undo_logs import UndoLog
from data.migrate.sql_coll import SQLcollector, SQLcollectors
from data.roots import decode_path, encode_path
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.base_dirs import BaseDirQueries
from general.log import log_error, log_info, log_print, log_warning
from general.name_utils import Names
from general.pdutil import ncols, nrows
from general.preview import Preview, pva
from general.singular_or_plural import sop
from general.valid_email import is_valid_email
from process.general.base_processor import FileProcessor
from process.general.pipeline import FilePipeline, SingleFilePipeline

class BasedirXLSImporter(FileProcessor):
    NCOLS = 4
    class Colnr(Enum):
        YEAR            = 0
        PERIOD          = 1
        FORMS_VERSION   = 2
        DIRECTORY       = 3
    expected_columns = {Colnr.YEAR: 'jaar', 
                        Colnr.PERIOD: 'periode', 
                        Colnr.FORMS_VERSION: 'forms_version', 
                        Colnr.DIRECTORY: 'directory', 
                        }
    def __init__(self):
        self.writer = None
        self.sheet = None
        self._error = ''
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        self.sql=SQLcollectors()# to use in migration script
        self.sql.add('base_dirs',
            SQLcollector({'insert':{'sql':'insert into BASEDIRS (id,year,period,forms_version,directory) values(?,?,?,?,?)'}, 
             'update':{'sql':'update BASEDIRS set year=?,period=?,forms_version=?,directory=? where id = ?'}}))
        super().__init__(description='Importeren basedirs')
    def __get(self, dataframe: pd.DataFrame, rownr: int, colnr: Colnr)->Any:
        return dataframe.at[rownr, self.expected_columns[colnr]]        
    def __add_sql(self, base_dir: BaseDir, is_new=True):
        if is_new:
            self.sql.insert('base_dirs', [base_dir.id, base_dir.year, base_dir.period, base_dir.forms_version, encode_path(base_dir.directory)])
        else:
            self.sql.update('base_dirs', [base_dir.year,base_dir.period, base_dir.forms_version, encode_path(base_dir.directory), base_dir.stud_nr])
    def __check_format(self, df: pd.DataFrame):    
        self._error = ''
        if ncols(df) != self.NCOLS:
            self._error = f'Onverwacht aantal kolommen ({ncols(df)}). Verwachting is {self.NCOLS}.'
            return False
        for column,expected_column in zip(df.columns, self.expected_columns.values()):
            if column.lower() != expected_column:
                self._error = f'Onverwachte kolom-header: {column}. Verwachte kolommen:\n\t{[self.expected_columns]}'
                return False
        if nrows(df) == 0:
            self._error = f'Niets om te importeren.'
            return False
        return True
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
    def __read_basedir(self, df: pd.DataFrame, row: int)->BaseDir:
        return BaseDir(year=int(self.__get(df,row, self.Colnr.YEAR)),
                        period = str(self.__get(df, row, self.Colnr.PERIOD)).strip(),
                        forms_version = self.__get(df, row, self.Colnr.FORMS_VERSION).strip(),
                        directory = decode_path(self.__get(df, row, self.Colnr.DIRECTORY).strip())
                       )        
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Tuple[int,int,int]:
        dataframe = pd.read_excel(filename)
        if dataframe.empty:
            log_error(f'Kan data niet laden uit {filename}.')
            return 0
        if not self.__check_format(dataframe):
            log_error(f'Kan basedir-gegevens niet importeren uit {filename}.\n\t\
                      {self._error}.')
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        for row in range(nrows(dataframe)):
            if not (base_dir := self.__read_basedir(dataframe, row)):
                log_error(f'Fout bij lezen rij {row}: {self._error}.')
            else:
                self.__check_and_store_basedir(base_dir, storage)
        return (self.n_new,self.n_modified,self.n_already_there)
        
def import_basedirs_XLS(xls_filename: str, storage: AAPAStorage, migrate_dir = None, preview=False):
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
            if migrate_dir:
                filename = Path(migrate_dir).resolve().joinpath('insert_basedirs.json')
                importer.sql.dump_to_file(filename)
                log_print(f'SQL data dumped to file {filename}')
            storage.commit()
