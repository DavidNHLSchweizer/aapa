from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.verslagen import Verslag
from data.general.const import FileType, MijlpaalBeoordeling, MijlpaalType
from data.classes.files import File
from database.classes.database import Database
import database.classes.dbConst as dbc
from database.aapa_database import AanvraagTableDefinition, FilesTableDefinition, MijlpaalDirectoryTableDefinition, UndoLogFilesTableDefinition, VerslagTableDefinition, get_sql_cases_for_int_type
from database.classes.sql_table import SQLcreateTable, SQLdropTable
from database.classes.sql_view import SQLcreateView, SQLdropView
from database.classes.table_def import ForeignKeyAction, TableDefinition
from data.general.class_codes import ClassCodes
from database.classes.view_def import ViewDefinition
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext

class DetailTableDefinition2(TableDefinition):
    def __init__(self, name: str, 
                 main_table_name: str, main_alias_id: str):
        super().__init__(name)
        self._detail_tables = {}
        self.add_column(main_alias_id, dbc.INTEGER, primary = True)
        self.add_column('detail_id', dbc.INTEGER, primary = True)          
        self.add_column('class_code', dbc.TEXT, primary = True)  
        self.add_foreign_key(main_alias_id, main_table_name, 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    def add_detail(self, detail_code: str, detail_table: TableDefinition):
        self._detail_tables[detail_code] = detail_table

class AanvraagDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('AANVRAGEN_DETAILS', main_table_name='AANVRAGEN', main_alias_id='aanvraag_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)

class MijlpaalDirectoriesDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('MIJLPAAL_DIRECTORIES_DETAILS', main_table_name='MIJLPAAL_DIRECTORIES', main_alias_id='mp_dir_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)

class StudentDirectoriesDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('STUDENT_DIRECTORIES_DETAILS', main_table_name='STUDENT_DIRECTORIES', main_alias_id='stud_dir_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(MijlpaalDirectory), detail_table=MijlpaalDirectoryTableDefinition)

class UndologsDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('UNDOLOGS_DETAILS', main_table_name='UNDOLOGS', main_alias_id='log_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(Aanvraag), detail_table=AanvraagTableDefinition)
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)
        self.add_detail(detail_code=ClassCodes.classtype_to_code(Verslag), detail_table=VerslagTableDefinition)

class VerslagenDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('VERSLAGEN_DETAILS', main_table_name='VERSLAGEN', main_alias_id='verslag_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)

class AanvragenFileOverzichtDefinition2(ViewDefinition):
    def __init__(self):
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType, 'filetype') 
        stud_name = '(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student'
        innerjoins = 'inner join AANVRAGEN_DETAILS as AD on A.ID=AD.aanvraag_id inner join FILES as F on F.ID=AD.detail_id'
        super().__init__('AANVRAGEN_FILE_OVERZICHT2', 
                         query=f'select A.id as aanvraag_id,{stud_name},titel, F.ID as file_id,F.filename as filename,{filetype_str} \
                                from AANVRAGEN as A {innerjoins} where AD.class_code="{ClassCodes.classtype_to_code(File)}" order by 2')

class StudentDirectoriesFileOverzichtDefinition2(ViewDefinition):
    def __init__(self):
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType, 'filetype') 
        mijlpaal_str = get_sql_cases_for_int_type('F.mijlpaal_type', MijlpaalType, 'mijlpaal') 
        status_str = get_sql_cases_for_int_type('sd.status', StudentDirectory.Status, 'dir_status') 
        query = \
f'select SD.id,SD.STUD_ID,SD.directory as student_directory,{status_str},MD.id as mp_id,MD.directory as mp_dir,F.ID as file_id,F.filename,{filetype_str},{mijlpaal_str} \
from STUDENT_DIRECTORIES as SD \
inner join STUDENT_DIRECTORIES_DETAILS as SDD on SD.id=SDD.stud_dir_id \
inner join MIJLPAAL_DIRECTORIES as MD on MD.id=SDD.detail_id \
inner join MIJLPAAL_DIRECTORIES_DETAILS as MDF on MD.ID=MDF.mp_dir_id \
inner join FILES as F on F.ID=MDF.detail_id'
        super().__init__('STUDENT_DIRECTORIES_FILE_OVERZICHT2', query=query)

class StudentMijlpaalDirectoriesOverzichtDefinition2(ViewDefinition):
    def __init__(self):
        mijlpaal_str = get_sql_cases_for_int_type('MPD.mijlpaal_type', MijlpaalType, 'mijlpaal_type') 
        query = f'select (select full_name from studenten as S where S.id=SD.stud_id) as student, MPD.datum, {mijlpaal_str}, MPD.kans, MPD.directory \
                from student_directories as SD \
                inner join STUDENT_DIRECTORIES_DETAILS as SDD on SD.ID=SDD.stud_dir_id \
                inner join MIJLPAAL_DIRECTORIES as MPD on MPD.ID=SDD.detail_id order by 1,3'
        super().__init__('STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT2', query=query)

class StudentVerslagenOverzichtDefinition2(ViewDefinition):
    #TODO: toevoegen filename en/of datum. Wat lastiger dan gedacht, voorlopig maar even weggelaten
    def __init__(self):
        verslag_type_str = get_sql_cases_for_int_type('V.verslag_type', MijlpaalType, 'verslag_type') 
        status_str = get_sql_cases_for_int_type('V.status', Verslag.Status, 'status') 
        beoordeling = get_sql_cases_for_int_type('V.beoordeling', MijlpaalBeoordeling, 'beoordeling')
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType,'filetype')
        query = f'select V.id as verslag_id, V.stud_id, (select full_name from STUDENTEN as S where S.id=V.stud_id) as student, V.datum, {verslag_type_str}, \
            (select name from BEDRIJVEN as B where B.id=V.bedrijf_id) as bedrijf, V.titel,V.kans, F.id as file_id, F.filename,{filetype_str},{status_str},{beoordeling} \
            from VERSLAGEN as V inner join VERSLAGEN_DETAILS as VD on VD.verslag_id = V.id inner join FILES as F on F.ID=VD.detail_id order by 3,4'        
        super().__init__('STUDENT_VERSLAGEN_OVERZICHT2', query=query)

class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True
    def _drop_views(self, database: Database):
        database.execute_sql_command(SQLdropView(AanvragenFileOverzichtDefinition2()))
        database.execute_sql_command(SQLdropView(StudentDirectoriesFileOverzichtDefinition2()))
        database.execute_sql_command(SQLdropView(StudentVerslagenOverzichtDefinition2()))
        database.execute_sql_command(SQLdropView(StudentMijlpaalDirectoriesOverzichtDefinition2()))
    def _create_aanvragen(self, database: Database):
        database.execute_sql_command(SQLdropTable(AanvraagDetailsTableDefinition()))
        database.execute_sql_command(SQLcreateTable(AanvraagDetailsTableDefinition()))
        database._execute_sql_command(
            f'INSERT into AANVRAGEN_DETAILS(aanvraag_id,detail_id,class_code) select aanvraag_id,file_id,"{ClassCodes.classtype_to_code(File)}" from AANVRAGEN_FILES')
    def _create_mijlpaal_directories(self, database: Database):
        database.execute_sql_command(SQLdropTable(MijlpaalDirectoriesDetailsTableDefinition()))
        database.execute_sql_command(SQLcreateTable(MijlpaalDirectoriesDetailsTableDefinition()))
        database._execute_sql_command(
            f'INSERT into MIJLPAAL_DIRECTORIES_DETAILS(mp_dir_id,detail_id,class_code) select mp_dir_id,file_id,"{ClassCodes.classtype_to_code(File)}" from MIJLPAAL_DIRECTORY_FILES')     
    def _create_student_directories(self, database: Database):
        database.execute_sql_command(SQLdropTable(StudentDirectoriesDetailsTableDefinition()))
        database.execute_sql_command(SQLcreateTable(StudentDirectoriesDetailsTableDefinition()))
        database._execute_sql_command(
            f'INSERT into STUDENT_DIRECTORIES_DETAILS(stud_dir_id,detail_id,class_code) select stud_dir_id,mp_dir_id,"{ClassCodes.classtype_to_code(MijlpaalDirectory)}" from STUDENT_DIRECTORY_DIRECTORIES')
    def _create_undologs(self, database: Database):
        database.execute_sql_command(SQLdropTable(UndologsDetailsTableDefinition()))
        database.execute_sql_command(SQLcreateTable(UndologsDetailsTableDefinition()))
        database._execute_sql_command(
            f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,aanvraag_id,"{ClassCodes.classtype_to_code(Aanvraag)}" from UNDOLOGS_AANVRAGEN')
        database._execute_sql_command(
            f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,file_id,"{ClassCodes.classtype_to_code(File)}" from UNDOLOGS_FILES')
        database._execute_sql_command(
            f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,verslag_id,"{ClassCodes.classtype_to_code(Verslag)}" from UNDOLOGS_VERSLAGEN')
    def _create_verslagen(self, database: Database):
        database.execute_sql_command(SQLdropTable(VerslagenDetailsTableDefinition()))
        database.execute_sql_command(SQLcreateTable(VerslagenDetailsTableDefinition()))
        database._execute_sql_command(
            f'INSERT into VERSLAGEN_DETAILS(verslag_id,detail_id,class_code) select verslag_id,file_id,"{ClassCodes.classtype_to_code(File)}" from VERSLAGEN_FILES')
    def _create_views(self, database: Database):
        database.execute_sql_command(SQLcreateView(AanvragenFileOverzichtDefinition2()))
        database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition2()))
        database.execute_sql_command(SQLcreateView(StudentVerslagenOverzichtDefinition2()))
        database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition2()))

    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self._drop_views(self.database)
        self._create_aanvragen(self.database)
        self._create_mijlpaal_directories(self.database)
        self._create_student_directories(self.database)
        self._create_undologs(self.database)
        self._create_verslagen(self.database)
        self._create_views(self.database)
        self.database.commit()
        return True
    