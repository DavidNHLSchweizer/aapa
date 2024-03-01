from data.classes.student_directories import StudentDirectory
from data.classes.verslagen import Verslag
from data.general.const import FileType, MijlpaalBeoordeling, MijlpaalType
from database.aapa_database import get_sql_cases_for_int_type
from database.classes.table_def import ForeignKeyAction, TableDefinition
from database.classes.view_def import ViewDefinition
import database.classes.dbConst as dbc

class DetailTableDefinition(TableDefinition):
    def __init__(self, name: str, 
                 main_table_name: str, main_alias_id: str, 
                 detail_table_name: str, detail_alias_id: str):
        super().__init__(name)
        self.add_column(main_alias_id, dbc.INTEGER, primary = True)
        self.add_column(detail_alias_id, dbc.INTEGER, primary = True)  
        self.add_foreign_key(main_alias_id, main_table_name, 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key(detail_alias_id, detail_table_name, 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)


class AanvraagFilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN_FILES', 
                         main_table_name='AANVRAGEN', main_alias_id='aanvraag_id',
                         detail_table_name='FILES', detail_alias_id='file_id')

class VerslagFilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('VERSLAGEN_FILES', 
                         main_table_name='VERSLAGEN', main_alias_id='verslag_id',
                         detail_table_name='FILES', detail_alias_id='file_id')

class UndoLogAanvragenTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS_AANVRAGEN', 
                         main_table_name='UNDOLOGS', main_alias_id='log_id', 
                         detail_table_name='AANVRAGEN', detail_alias_id='aanvraag_id')
       
class UndoLogVerslagenTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS_VERSLAGEN', 
                         main_table_name='UNDOLOGS', main_alias_id='log_id', 
                         detail_table_name='VERSLAGEN', detail_alias_id='verslag_id')

class UndoLogFilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS_FILES', 
                         main_table_name='UNDOLOGS', main_alias_id='log_id', 
                         detail_table_name='FILES', detail_alias_id='file_id')

class StudentDirectory_DirectoriesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('STUDENT_DIRECTORY_DIRECTORIES', 
                         main_table_name='STUDENT_DIRECTORIES', main_alias_id='stud_dir_id',
                         detail_table_name='MIJLPAAL_DIRECTORY', detail_alias_id='mp_dir_id')

class MijlpaalDirectory_FilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('MIJLPAAL_DIRECTORY_FILES', 
                         main_table_name='MIJLPAAL_DIRECTORIES', main_alias_id='mp_dir_id',
                         detail_table_name='FILES', detail_alias_id='file_id')

#---views
        
class oldAanvragenFileOverzichtDefinition(ViewDefinition):
    def __init__(self):
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType, 'filetype') 
        stud_name = '(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student'
        innerjoins = ' inner join AANVRAGEN_FILES as AF on A.ID=AF.aanvraag_id inner join FILES as F on F.ID=AF.file_id'
        super().__init__('AANVRAGEN_FILE_OVERZICHT', 
                         query=f'select A.id as aanvraag_id,{stud_name},titel, F.ID as file_id,F.filename as filename,{filetype_str} \
                                from AANVRAGEN as A {innerjoins} order by 2')
        

class oldStudentMijlpaalDirectoriesOverzichtDefinition(ViewDefinition):
    def __init__(self):
        mijlpaal_str = get_sql_cases_for_int_type('MPD.mijlpaal_type', MijlpaalType, 'mijlpaal_type') 
        query = f'select (select full_name from studenten as S where S.id=SD.stud_id) as student, MPD.datum, {mijlpaal_str}, MPD.kans, MPD.directory \
                from student_directories as SD \
                inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.ID=SDD.stud_dir_id \
                inner join MIJLPAAL_DIRECTORIES MPD on MPD.ID=SDD.mp_dir_id order by 1,3'
        super().__init__('STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT', query=query)

class oldStudentVerslagenOverzichtDefinition(ViewDefinition):
    #TODO: toevoegen filename en/of datum. Wat lastiger dan gedacht, voorlopig maar even weggelaten
    def __init__(self):
        verslag_type_str = get_sql_cases_for_int_type('V.verslag_type', MijlpaalType, 'verslag_type') 
        status_str = get_sql_cases_for_int_type('V.status', Verslag.Status, 'status') 
        beoordeling = get_sql_cases_for_int_type('V.beoordeling', MijlpaalBeoordeling, 'beoordeling')
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType,'filetype')
        query = f'select V.id as verslag_id, V.stud_id, (select full_name from STUDENTEN as S where S.id=V.stud_id) as student, V.datum, {verslag_type_str}, \
            (select name from BEDRIJVEN as B where B.id=V.bedrijf_id) as bedrijf, V.titel,V.kans, F.id as file_id, F.filename,{filetype_str},{status_str},{beoordeling} \
            from VERSLAGEN as V inner join VERSLAGEN_FILES as VF on VF.verslag_id = V.id inner join FILES as F on F.ID=VF.file_id order by 3,4' 
        
        super().__init__('STUDENT_VERSLAGEN_OVERZICHT', query=query)

class oldStudentDirectoriesFileOverzichtDefinition(ViewDefinition):
    def __init__(self):
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType, 'filetype') 
        mijlpaal_str = get_sql_cases_for_int_type('F.mijlpaal_type', MijlpaalType, 'mijlpaal') 
        status_str = get_sql_cases_for_int_type('sd.status', StudentDirectory.Status, 'dir_status') 
        query = \
f'select SD.id,SD.STUD_ID,SD.directory as student_directory,{status_str},MD.id as mp_id,MD.directory as mp_dir,F.ID as file_id,F.filename,{filetype_str},{mijlpaal_str} \
from STUDENT_DIRECTORIES as SD \
inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.id=SDD.stud_dir_id \
inner join MIJLPAAL_DIRECTORIES as MD on MD.id=SDD.mp_dir_id \
inner join MIJLPAAL_DIRECTORY_FILES as MDF on MD.ID=MDF.mp_dir_id \
inner join FILES as F on F.ID=MDF.file_id'
        super().__init__('STUDENT_DIRECTORIES_FILE_OVERZICHT', query=query)
