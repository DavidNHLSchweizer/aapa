from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.verslagen import Verslag
from data.general.const import FileType, MijlpaalBeoordeling, MijlpaalType
from data.classes.files import File
from database.classes.database import Database
import database.classes.dbConst as dbc
from database.aapa_database import AanvraagDetailsTableDefinition, AanvraagTableDefinition, AanvragenFileOverzichtDefinition2, DetailTableDefinition2, FilesTableDefinition, MijlpaalDirectoriesDetailsTableDefinition, MijlpaalDirectoryTableDefinition, StudentDirectoriesDetailsTableDefinition, StudentDirectoriesFileOverzichtDefinition2, StudentMijlpaalDirectoriesOverzichtDefinition2, StudentVerslagenOverzichtDefinition2, UndoLogFilesTableDefinition, UndologsDetailsTableDefinition, VerslagTableDefinition, VerslagenDetailsTableDefinition, get_sql_cases_for_int_type
from database.classes.sql_table import SQLcreateTable, SQLdropTable
from database.classes.sql_view import SQLcreateView, SQLdropView
from database.classes.table_def import ForeignKeyAction, TableDefinition
from data.general.class_codes import ClassCodes
from database.classes.view_def import ViewDefinition
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext

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

    def migrate(self, database: Database):
        self._drop_views(self.database)
        self._create_aanvragen(self.database)
        self._create_mijlpaal_directories(self.database)
        self._create_student_directories(self.database)
        self._create_undologs(self.database)
        self._create_verslagen(self.database)
        self._create_views(self.database)
        self.database.commit()

    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.migrate(self.database)
        return True
    