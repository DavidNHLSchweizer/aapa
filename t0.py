from datetime import datetime
from pathlib import Path
import data.AAPdatabase as db
import data.AAPcrud as dbc 
from data.aanvraag_info import Bedrijf, FileInfo, FileType, StudentInfo, AanvraagDocumentInfo
from database.database import Database
from database.dump import DatabaseDumper
import random


DBNAME =  'AAP.DB'

def create_database(name, recreate = False):
    if recreate or not Path(name).is_file():
        print('RECREATION DATABASE')
        return  db.AAPDatabase.create_from_schema(db.AAPSchema(), name)
    else:
        print('OPENING DATABASE')
        return  db.AAPDatabase(name)

def create_bedrijven(database: Database):
    bc = dbc.CRUD_bedrijven(database)
    bc.create(Bedrijf('promo'))
    bc.create(Bedrijf('cheapo'))
    bc.create(Bedrijf('promo Drom'))
    bc.create(Bedrijf('campina'))
    database.commit()
    DatabaseDumper(database).DumpTable('BEDRIJVEN')

def test_bedrijven(database: Database):
    bc = dbc.CRUD_bedrijven(database)
    bc.update(Bedrijf('Bloody Mary', id=3))
    database.commit()
    b = bc.read(2)
    print('BEDRIJF 2: ', b)
    bc.delete(b)
    database.commit()
    DatabaseDumper(database).DumpTable('BEDRIJVEN')

def create_files(database: Database):
    fc = dbc.CRUD_files(database)
    fc.create(FileInfo('jezusredt.htm', datetime.strptime('2-3-1957 10:11:12', FileInfo.DATETIME_FORMAT), FileType.MAIL_HTM))
    fc.create(FileInfo('jezusredtniet.pdf', datetime.strptime('2-3-1962 9:9:9', FileInfo.DATETIME_FORMAT), FileType.OORDEEL_PDF))
    fc.create(FileInfo('aanvraag1.pdf', datetime.now(), FileType.AANVRAAG_PDF))
    fc.create(FileInfo('aanvraag2.pdf', datetime.now(), FileType.AANVRAAG_PDF))
    fc.create(FileInfo('jezusredt.docx', datetime.now(), FileType.OORDEEL_DOCX))
    fc.create(FileInfo('jezusredt.pdf', datetime.now(), FileType.OORDEEL_PDF))
    fc.create(FileInfo('aanvraag4.pdf', datetime.now(), FileType.AANVRAAG_PDF))
    fc.create(FileInfo('aanvraag3.pdf', datetime.now(), FileType.AANVRAAG_PDF))
    database.commit()
    DatabaseDumper(database).DumpTable('FILES')

def test_files(database: Database):
    fc = dbc.CRUD_files(database)
    f = fc.read('jezusredtniet.pdf')
    print('gelezen: ', f)
    f.timestamp = datetime.now()
    print(' modified: ', f)
    fc.update(f)
    database.commit()
    fc.delete(f)
    database.commit()
    DatabaseDumper(database).DumpTable('FILES')

def create_studenten(database: Database):
    sc = dbc.CRUD_studenten(database)
    sc.create(StudentInfo('Erik de Noorman', '123456', '06-07-08-09-10', 'erik@noot.mies.com'))
    sc.create(StudentInfo('Erica de Zuurvrouw', '123458', '16-17-18-19-20', 'zuur@noot.mies.com'))
    sc.create(StudentInfo('ProtoPlasma', '123459', '96-17-18-19-20', 'plasma@vuur.mies.com'))
    sc.create(StudentInfo('Zwerica Zwanepoel', '423459', '86-87-18-19-20', 'zwerica@vuur.mies.com'))
    database.commit()
    DatabaseDumper(database).DumpTable('STUDENTEN')

def test_studenten(database: Database):
    sc = dbc.CRUD_studenten(database)
    f = sc.read('123456')
    print('gelezen: ', f)
    f.email = 'erik@shotmail.stom'
    sc.update(f)
    sc.delete(sc.read('123459'))
    database.commit()
    DatabaseDumper(database).DumpTable('STUDENTEN')

def create_aanvragen(database: Database):
    ac = dbc.CRUD_aanvragen(database)
    sc = dbc.CRUD_studenten(database)
    fc = dbc.CRUD_files(database)
    bc = dbc.CRUD_bedrijven(database)

    def create(fileinfo, student, bedrijf, datum, titel, beoordeling=0):
        aanvraag = AanvraagDocumentInfo(fileinfo, student, bedrijf, datum,  titel, beoordeling)
        ac.create(aanvraag)

    create(fc.read('aanvraag1.pdf'), sc.read('423459'), bc.read(3), '11-11-2022', 'De lippen van Amalia', 10)
    create(fc.read('aanvraag2.pdf'), sc.read('123458'), bc.read(1), '13-11-2022', 'De handen van Amalia', 8)
    create(fc.read('aanvraag3.pdf'), sc.read('123456'), bc.read(2), '15-11-2022', 'De benen van Amalia')
    create(fc.read('aanvraag4.pdf'), sc.read('123459'), bc.read(2), '18-11-2022',  'De voeten van Amalia')
    database.commit()
    DatabaseDumper(database).DumpTable('AANVRAGEN')

def test_aanvragen(database: Database):
    ac = dbc.CRUD_aanvragen(database)
    aanvraag = ac.read(1)
    print(aanvraag)
    aanvraag = ac.read(3)
    print(aanvraag)
    aanvraag.titel='de onderbroek'
    ac.update(aanvraag)
    database.commit()
    # DatabaseDumper(database).DumpTable('AANVRAGEN')

def create_all(database: Database):
    create_studenten(database)
    create_bedrijven(database)
    create_files(database)
    create_aanvragen(database)

database = create_database(DBNAME, False)
#create_all(database)
DatabaseDumper(database).DumpTables([])
test_aanvragen(database)
# test_files(True)
# dbd.DumpTables()
# fc = dbc.CRUD_files(database)
# f = fc.read('jezusredt.pdf')
# print(f)
# test_aanvragen(True)

database.close()

