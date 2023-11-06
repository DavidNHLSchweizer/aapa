from enum import IntEnum
from data.AAPdatabase import AanvraagTableDefinition, StudentTableDefinition, VerslagTableDefinition
from database.SQL import SQLcreate
from database.database import Database
from database.tabledef import ForeignKeyAction

# Wijzigingen in 1.19 voor migratie:
#
# studenten krijgt ook zijn eigen ID.
# toevoegen verslagen tabel
#
def modify_studenten_table(database: Database):
    print('adding primary key to STUDENTEN table.')
    database._execute_sql_command('alter table STUDENTEN RENAME TO OLD_STUDENTEN')
    print('creating the new table')
    database.execute_sql_command(SQLcreate(StudentTableDefinition()))
    database._execute_sql_command('insert into STUDENTEN(stud_nr,full_name,first_name,email,tel_nr) select stud_nr,full_name,first_name,email,tel_nr from OLD_STUDENTEN', [])
    database._execute_sql_command('drop table OLD_STUDENTEN')
    print('end adding primary key to STUDENTEN table.')

def modify_aanvragen_table(database: Database):
    print('modifying AANVRAGEN table.')
    database._execute_sql_command('alter table AANVRAGEN RENAME TO OLD_AANVRAGEN')
    print('creating the new table')
    aanvragen_table = AanvraagTableDefinition() 
    database.execute_sql_command(SQLcreate(aanvragen_table))
    aanvragen_table.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    aanvragen_table.add_foreign_key('bedrijf_id', 'BEDRIJVEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    #copying the data
    database._execute_sql_command('insert into AANVRAGEN(id,bedrijf_id,datum_str,titel,aanvraag_nr,status,beoordeling)'+ \
                                  ' select id,bedrijf_id,datum_str,titel,aanvraag_nr,status,beoordeling from OLD_AANVRAGEN', [])
    print('adding new STUDENT references to AANVRAGEN table.')
    sql = 'SELECT AANVRAGEN.id,STUDENTEN.id FROM AANVRAGEN,OLD_AANVRAGEN,STUDENTEN \
        WHERE ((STUDENTEN.stud_nr=OLD_AANVRAGEN.stud_nr) AND (AANVRAGEN.ID=OLD_AANVRAGEN.ID))'
    for row in database._execute_sql_command(sql, [], True):
        database._execute_sql_command('update AANVRAGEN set stud_id=? where id=?', [row[1], row[0]])
    database._execute_sql_command('drop table OLD_AANVRAGEN')
    print('end modifying STUDENT references to AANVRAGEN table.')
    print('end modifying AANVRAGEN table.')

# toevoegen VERSLAGEN tabel
def create_new_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN')
    verslag_table = VerslagTableDefinition()        
    verslag_table.add_foreign_key('id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreate(verslag_table))
    print('--- klaar toevoegen nieuwe tabellen')

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        modify_studenten_table(database)
        modify_aanvragen_table(database)    
        create_new_tables(database)


