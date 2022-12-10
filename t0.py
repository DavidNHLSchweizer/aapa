from datetime import datetime
from pathlib import Path
import data.AAPdatabase as db
import data.AAPcrud as dbc 
from data.aanvraag_info import Bedrijf, FileInfo, FileType, StudentInfo
from database.dump import DatabaseDumper
import random


DBNAME =  'AAP.DB'

recreate = True
if recreate or not Path(DBNAME).is_file():
    database = db.AAPDatabase.create_from_schema(db.AAPSchema(), 'AAP.db')
else:
    database = db.AAPDatabase(DBNAME)
dbd = DatabaseDumper(database)

def test_bedrijven(recreate):
    bc = dbc.CRUD_bedrijven(database)

    if recreate:
        bc.create(Bedrijf('promo'))
        bc.create(Bedrijf('cheapo'))
        bc.create(Bedrijf('promo Drom'))
        bc.create(Bedrijf('campina'))
        database.commit()
    dbd.DumpTables(['BEDRIJVEN'])
    bc.update(Bedrijf('Bloody Mary', id=3))
    database.commit()
    dbd.DumpTables(['BEDRIJVEN'])

    b = bc.read(2)
    print('BEDRIJF 2: ', b)
    dbd.DumpTables(['BEDRIJVEN'])
    bc.delete(b)
    database.commit()
    dbd.DumpTables(['BEDRIJVEN'])
def test_files(recreate):
    fc = dbc.CRUD_files(database)
    if recreate:
        fc.create(FileInfo('jezusredt.htm', datetime.strptime('2-3-1957 10:11:12', FileInfo.DATETIME_FORMAT), FileType.MAIL_HTM))
        fc.create(FileInfo('jezusredtniet.pdf', datetime.strptime('2-3-1962 9:9:9', FileInfo.DATETIME_FORMAT), FileType.OORDEEL_PDF))
        fc.create(FileInfo('jezusredt.docx', datetime.now(), FileType.OORDEEL_DOCX))
        fc.create(FileInfo('jezusredt.pdf', datetime.now(), FileType.OORDEEL_PDF))
        database.commit()
    dbd.DumpTables(['FILES'])
    f = fc.read('jezusredtniet.pdf')
    print('gelezen: ', f)
    f.timestamp = datetime.now()
    print(' modified: ', f)
    fc.update(f)
    database.commit()
    dbd.DumpTables(['FILES'])
    fc.delete(f)
    database.commit()
    dbd.DumpTables(['FILES'])
def test_studenten(recreate):
    sc = dbc.CRUD_studenten(database)
    if recreate: #TODO: WAAROM WERKT DIT NIET? (probeer directe SQL in de CRUD!)
        sc.create(StudentInfo('Erik de Noorman', '123456', '06-07-08-09-10', 'erik@noot.mies.com'))
        sc.create(StudentInfo('Erica de Zuurvrouw', '123458', '16-17-18-19-20', 'zuur@noot.mies.com'))
        sc.create(StudentInfo('ProtoPlasma', '123459', '96-17-18-19-20', 'plasma@vuur.mies.com'))
        sc.create(StudentInfo('Zwerica Zwanepoel', '423459', '86-87-18-19-20', 'zwerica@vuur.mies.com'))
        database.commit()
    dbd.DumpTables(['STUDENTEN'])
    f = sc.read('123456')
    print('gelezen: ', f)
    
# test_files(True)
dbd.DumpTables(['FILES'])
fc = dbc.CRUD_files(database)
f = fc.read('jezusredt.pdf')
print(f)
test_studenten(True)

database.close()

