from enum import IntEnum
from data.AAPdatabase import AanvraagTableDefinition, ActionLogAanvragenTableDefinition, ActionLogFilesTableDefinition, ActionLogTableDefinition, FilesTableDefinition, MilestoneTableDefinition, VerslagTableDefinition
from data.classes.files import File
from database.SQL import SQLcreate, SQLinsert
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

def create_new_aanvragen_table(database: Database):
    print('modifying AANVRAGEN table (splitting data with MILESTONES).')
    database._execute_sql_command('alter table AANVRAGEN RENAME TO OLD_AANVRAGEN')
    print('creating the new table')
    database.execute_sql_command(SQLcreate(AanvraagTableDefinition()))
    print('divide data between MILESTONES en AANVRAGEN')
    milestone_table = MilestoneTableDefinition()
    aanvraag_table = AanvraagTableDefinition()
    database.disable_foreign_keys()
    for row in database._execute_sql_command('select id,stud_nr, bedrijf_id, datum_str, titel, aanvraag_nr, status, beoordeling from OLD_AANVRAGEN', [], True):
        milestone_id = row['id']
        database.execute_sql_command(SQLinsert(milestone_table, 
                                    columns=['id', 'type_description', 'stud_nr', 'titel', 'status', 'beoordeling'], 
                                    values=[milestone_id, 'aanvraag', row['stud_nr'], row['titel'], row['status'], row['beoordeling']]))
        database.execute_sql_command(SQLinsert(aanvraag_table,
                                    columns=['milestone_id', 'bedrijf_id', 'datum_str', 'aanvraag_nr'], 
                                    values=[milestone_id, row['bedrijf_id'], row['datum_str'], row['aanvraag_nr']]))
    database._execute_sql_command('drop table OLD_AANVRAGEN')
    database.enable_foreign_keys()
    print('end modifying AANVRAGEN table.')

# def migrate_aanvragen(database: Database):
#     print('migratie data AANVRAGEN naar MILESTONES')
#     database._execute_sql_command('insert into MILESTONES(id, type_description, stud_nr, titel, status, beoordeling)' +\
#                                   'select id, "aanvraag", stud_nr, titel, status, beoordeling from AANVRAGEN', [])
#     print('--- klaar migratie data AANVRAGEN naar MILESTONES')

def migrate_database(database: Database):
    create_new_tables(database)
    create_new_aanvragen_table(database)
