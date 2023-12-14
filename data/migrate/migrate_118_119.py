from data.aapa_database import AanvraagFilesTableDefinition, AanvraagTableDefinition, AanvragenFileOverzichtDefinition, AanvragenOverzichtDefinition, FilesTableDefinition, \
                            StudentTableDefinition, UndoLogTableDefinition
from data.classes.const import MijlpaalType
from data.classes.files import File
from database.sql_table import SQLcreateTable
from database.database import Database
from database.sql_view import SQLcreateView
from database.table_def import TableDefinition
from general.name_utils import Names
import database.dbConst as dbc
from general.timeutil import TSC

# Wijzigingen in 1.19 voor migratie:
#
# aanpassen tijden in database (sorteerbaar gemaakt)
# studenten krijgt ook zijn eigen ID. Aanpassingen aan AANVRAGEN hiervoor
# toevoegen status kolom in STUDENTEN, remove tel_nr kolom
# link files met aanvragen wordt met nieuwe koppeltabel AANVRAGEN_FILES. Aanpassingen aan FILES en AANVRAGEN hiervoor
# toevoegen mijlpaal_type aan FILES
# voorbereiding: aanvraag_nr -> kans
# creating AANVRAGEN_OVERZICHT en AANVRAGEN_FILES overzicht
# correctie enige voornamen van studenten
# naamswijziging ACTIONLOG->UNDOLOG
#
def modify_studenten_table(database: Database):
    print('adding primary key to STUDENTEN table, also adding status and remove telnr.')
    database._execute_sql_command('alter table STUDENTEN RENAME TO OLD_STUDENTEN')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(StudentTableDefinition()))
    database._execute_sql_command('insert into STUDENTEN(stud_nr,full_name,first_name,email) select stud_nr,full_name,first_name,email from OLD_STUDENTEN', [])
    database._execute_sql_command('drop table OLD_STUDENTEN')
    print('end adding primary key to STUDENTEN table, also adding status and remove telnr.')

def modify_aanvragen_table(database: Database):
    print('modifying AANVRAGEN table.')
    database._execute_sql_command('alter table AANVRAGEN RENAME TO OLD_AANVRAGEN')
    print('creating the new table')
    aanvragen_table = AanvraagTableDefinition() 
    database.execute_sql_command(SQLcreateTable(aanvragen_table))
    #copying the data
    database._execute_sql_command('insert into AANVRAGEN(id,bedrijf_id,datum_str,titel,status,beoordeling,kans,versie)'+ \
                                  ' select id,bedrijf_id,datum_str,titel,status,beoordeling,aanvraag_nr,aanvraag_nr from OLD_AANVRAGEN', [])
    print('adding new STUDENT references to AANVRAGEN table.')
    sql = 'SELECT AANVRAGEN.id,STUDENTEN.id FROM AANVRAGEN,OLD_AANVRAGEN,STUDENTEN \
        WHERE ((STUDENTEN.stud_nr=OLD_AANVRAGEN.stud_nr) AND (AANVRAGEN.ID=OLD_AANVRAGEN.ID))'
    for row in database._execute_sql_command(sql, [], True):
        database._execute_sql_command('update AANVRAGEN set stud_id=? where id=?', [row[1], row[0]])
    database._execute_sql_command('drop table OLD_AANVRAGEN')
    #kans en versie komt niet echt uit de verf, maar dat is lastig oplosbaar, laat eerst maar zo. 
    print('end modifying STUDENT references to AANVRAGEN table.')
    print('end modifying AANVRAGEN table.')

class OldFilesTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('filename', dbc.TEXT)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('digest', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)
        self.add_column('aanvraag_id', dbc.INTEGER)

def transform_time_str(value: str)->str:
    return TSC.timestamp_to_sortable_str(TSC.str_to_timestamp(value))

def modify_files_table(database: Database):
    print('modifying FILES table.')
    database._execute_sql_command('alter table FILES RENAME TO OLD_FILES')
    # print('copying the timestamps to AANVRAGEN table.')
    # database._execute_sql_command(f'update aanvragen set datum = (SELECT timestamp from OLD_FILES WHERE AANVRAAG_ID=AANVRAGEN.ID)')
    print('creating the new FILES table')
    database.execute_sql_command(SQLcreateTable(FilesTableDefinition()))
    #copying the data except the timestamp
    database._execute_sql_command('insert into FILES(id,filename, digest,filetype)'+ \
                                  ' select id,filename, digest,filetype from OLD_FILES')
    #copying and transforming the timestamps and adding mijlpaal_type, so far just AANVRAAG
    for row in database._execute_sql_command('select id, timestamp, filetype, filename from OLD_FILES', [], True):
        database._execute_sql_command('update FILES set timestamp=?,mijlpaal_type=? where id=?', 
                                      [transform_time_str(row['timestamp']), MijlpaalType.AANVRAAG, row['id']]) 
    print('copying the timestamps to AANVRAGEN table.')
    database._execute_sql_command(f'update aanvragen set datum = (SELECT timestamp from OLD_FILES WHERE AANVRAAG_ID=AANVRAGEN.ID and filetype=?)',
                                  [File.Type.AANVRAAG_PDF])
    # transforming the timestamps
    for row in database._execute_sql_command('select id, datum from AANVRAGEN', [], True):
        database._execute_sql_command('update AANVRAGEN set datum=? where id=?', [transform_time_str(row['datum']), row['id']]) 
    
    print('creating new AANVRAGEN_FILES table')
    database.execute_sql_command(SQLcreateTable(AanvraagFilesTableDefinition()))
    #copying the data
    database._execute_sql_command('insert into AANVRAGEN_FILES(aanvraag_id,file_id)'+ \
                                  ' select aanvraag_id,id from OLD_FILES where aanvraag_id != ?', [-1])
    database._execute_sql_command('drop table OLD_FILES')
    print('end creating AANVRAGEN_FILES table.')
    print('end modifying FILES table.')

def create_views(database: Database):
    print('creating views')
    print('aanvragen overzichten')
    database.execute_sql_command(SQLcreateView(AanvragenOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(AanvragenFileOverzichtDefinition()))
    print('--- ready creating views')

#aanpassen voornamen waar nodig
def correct_first_names(database: Database):
    print('correcting incorrect first names in STUDENTEN')
    for row in database._execute_sql_command('select id,full_name,first_name from STUDENTEN', [], True):
        parsed = Names.parsed(row['full_name'])
        if parsed.first_name != row['first_name']:
            print(f'\tCorrecting {row["full_name"]}')
            database._execute_sql_command('update STUDENTEN set first_name=? where id=?', [parsed.first_name, row['id']])
    print('--- ready incorrect first names in STUDENTEN')

#rename actionlogs tables to undologs
def rename_action_logs(database: Database):
    print('adapting ACTIONLOG tables.')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(UndoLogTableDefinition()))    
    print('copy data and transform timestrings to sortable format in UNDOLOGS table.')
    for row in database._execute_sql_command('select id,description,action,user,date,can_undo from ACTIONLOG', [], True):
        database._execute_sql_command('insert into UNDOLOGS VALUES (?,?,?,?,?,?)',
                                      [row['id'], row['description'], row['action'], 
                                       row['user'], transform_time_str(row['date']), row['can_undo']])    
    database._execute_sql_command('drop table ACTIONLOG')
    database._execute_sql_command('alter table ACTIONLOG_AANVRAGEN RENAME TO UNDOLOGS_AANVRAGEN')
    database._execute_sql_command('alter table ACTIONLOG_FILES RENAME TO UNDOLOGS_FILES')
    print('--- ready adapting ACTIONLOG tables')

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        modify_studenten_table(database)
        modify_aanvragen_table(database)    
        modify_files_table(database)
        create_views(database)
        correct_first_names(database)
        rename_action_logs(database)
