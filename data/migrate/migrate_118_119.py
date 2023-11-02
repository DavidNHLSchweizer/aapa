from enum import IntEnum
from data.AAPdatabase import ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition, FilesTableDefinition, MilestoneTableDefinition, VerslagTableDefinition
from data.classes.files import File
from database.SQL import SQLcreate
from database.database import Database
from database.tabledef import ForeignKeyAction
from data.classes.aanvragen import Aanvraag

# Wijzigingen in 1.19 voor migratie:
#
# toevoegen MILESTONES tabel 
# toevoegen VERSLAGEN tabel
# kopieren AANVRAGEN tabel (gedeeltelijk) naar MILESTONES, voorlopig nog niet vervangen

def create_new_tables(database: Database):
    print('toevoegen nieuwe tabel MILESTONES')
    verslag_table = MilestoneTableDefinition()        
    verslag_table.add_foreign_key('stud_nr', 'STUDENTEN', 'stud_nr', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreate(verslag_table))
    print('toevoegen nieuwe tabel VERSLAGEN')
    verslag_table = VerslagTableDefinition()        
    verslag_table.add_foreign_key('milestone_id', 'MILESTONES', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreate(verslag_table))
    print('--- klaar toevoegen nieuwe tabellen')

def migrate_aanvragen(database: Database):
    print('migratie data AANVRAGEN naar MILESTONES')
    database._execute_sql_command('insert into MILESTONES(id, type_description, stud_nr, titel, status, beoordeling)' +\
                                  'select id, "aanvraag", stud_nr, titel, status, beoordeling from AANVRAGEN', [])
    print('--- klaar migratie data AANVRAGEN naar MILESTONES')



def migrate_database(database: Database):
    create_new_tables(database)
    migrate_aanvragen(database)
