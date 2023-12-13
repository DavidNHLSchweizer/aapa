from typing import Tuple
from enum import Enum
from typing import Any

import pandas as pd
from data.classes.studenten import Student
from data.classes.undo_logs import UndoLog
from data.migrate.sql_coll import SQLcollector
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.studenten import StudentQueries
from general.log import log_error, log_info, log_print, log_warning
from general.name_utils import Names
from general.pdutil import ncols, nrows
from general.preview import Preview, pva
from general.singular_or_plural import sop
from general.valid_email import is_valid_email
from process.general.base_processor import FileProcessor
from process.general.pipeline import FilePipeline, SingleFilePipeline


class StudentenXLSImporter(FileProcessor):
    NCOLS = 5
    class Colnr(Enum):
        ACHTERNAAM   = 0
        VOORNAAM     = 1
        STUDNR       = 2
        EMAIL        = 3
        STATUS       = 4
    STATUS_CODES = {'aanvraag': Student.Status.AANVRAAG, 'bezig': Student.Status.BEZIG, 'afgestudeerd': Student.Status.AFGESTUDEERD,'gestopt': Student.Status.GESTOPT,}
    expected_columns = {Colnr.ACHTERNAAM: 'achternaam', 
                        Colnr.VOORNAAM: 'voornaam', 
                        Colnr.STUDNR: 'studnr', 
                        Colnr.EMAIL: 'email', 
                        Colnr.STATUS: 'status'}
    def __init__(self):
        self.writer = None
        self.sheet = None
        self._error = ''
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        self.sql=SQLcollector(# to use in migration script
            insert_str='insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)', 
            update_str='update STUDENTEN set full_name=?,first_name=?,email=?,status=? where stud_nr = ?')        
        super().__init__(description='Importeren studenten')
    def __get(self, dataframe: pd.DataFrame, rownr: int, colnr: Colnr)->Any:
        return dataframe.at[rownr, self.expected_columns[colnr]]        
    def __add_sql(self, student: Student, is_new=True):
        if is_new:
            self.sql.insert([student.id, student.stud_nr, student.full_name, student.first_name, student.email, int(student.status)])
        else:
            self.sql.update([student.full_name, student.first_name, student.email, int(student.status), student.stud_nr])
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
    def __check_and_store_student(self, student: Student, storage: AAPAStorage)->Any:
        def check_diff(student: Student, stored: Student, attrib: str)->bool:
            a1 = str(getattr(student, attrib, None))
            a2 = str(getattr(stored, attrib, None))
            if  a1 != a2:
                log_warning(f'\tVerschil in {attrib}: {a1}, {a2} in database.')
                return True
            return False
        queries: StudentQueries = storage.queries('studenten')
        if stored:=queries.find_student_by_name_or_email(student):
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
    def __read_student(self, df: pd.DataFrame, row: int)->Student:
        full_name = Names.full_name(self.__get(df,row,self.Colnr.VOORNAAM), 
                                                 self.__get(df,row,self.Colnr.ACHTERNAAM))
        email = self.__get(df,row, self.Colnr.EMAIL)
        if not is_valid_email(email):
            log_warning(f'Ongeldige email {self.__get(df,row,self.Colnr.EMAIL)} voor student {full_name}')
        return Student(full_name=full_name,
                       first_name = self.__get(df,row,self.Colnr.VOORNAAM), 
                       stud_nr=str(self.__get(df,row, self.Colnr.STUDNR)), 
                       email=email,
                       status = self.STATUS_CODES.get(self.__get(df, row, self.Colnr.STATUS), Student.Status.UNKNOWN)
                       )        
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Tuple[int,int,int]:
        dataframe = pd.read_excel(filename)
        if dataframe.empty:
            log_error(f'Kan data niet laden uit {filename}.')
            return 0
        if not self.__check_format(dataframe):
            log_error(f'Kan studentgegevens niet importeren uit {filename}.\n\t\
                      {self._error}.')
        self.n_new = 0
        self.n_modified = 0
        self.n_already_there = 0
        for row in range(nrows(dataframe)):
            if not (student := self.__read_student(dataframe, row)):
                log_error(f'Fout bij lezen rij {row}: {self._error}.')
            else:
                self.__check_and_store_student(student, storage)
        self.sql.dump_to_file('insert_students.json')
        return (self.n_new,self.n_modified,self.n_already_there)
        
def import_studenten_XLS(xls_filename: str, storage: AAPAStorage, preview=False):
    importer = StudentenXLSImporter()
    pipeline = SingleFilePipeline('Importeren studenten uit XLS bestand', importer, 
                                  storage, activity=UndoLog.Action.NOLOG)
    with Preview(preview,storage, 'Importeren studenten'):
        (n_new,n_modified,n_already_there)=pipeline.process(xls_filename, preview=preview)
        if n_new == 0:
            log_print(f'Geen nieuwe studenten om te importeren ({n_already_there} al in database, {n_modified} aangepast met nieuwe gegevens).')
        else:
            log_print(f'{sop(n_new, "student", "studenten", prefix="nieuwe ")} {pva(preview, "te importeren", "geimporteerd")} uit {xls_filename}.')
            log_print(f'{sop(n_modified, "student", "studenten")} {pva(preview, "aan te passen", "aangepast")} volgens {xls_filename}.')
            log_print(f'{sop(n_already_there, "student", "studenten")} al in database.')
            log_print(f'{sop(n_new+n_modified, "student", "studenten")} {pva(preview, "te importeren of aan te passen", "geimporteerd of aangepast")} volgens {xls_filename}.')
    storage.commit()
