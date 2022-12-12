from datetime import datetime
from pathlib import Path
import sys
import data.AAPdatabase as db
from storage import AAPStorage
from data.aanvraag_info import AanvraagBeoordeling, AanvraagStatus, Bedrijf, FileInfo, FileType, StudentInfo, AanvraagInfo
from database.database import Database
from database.dump import DatabaseDumper
from files.import_data import import_aanvraag
from files.report_data import AanvraagDataXLSReporter, report_aanvragen_XLS


DBNAME =  'AAP.DB'

def create_database(name, recreate = False)->Database:
    if recreate or not Path(name).is_file():
        print('RECREATION DATABASE')
        return  db.AAPDatabase.create_from_schema(db.AAPSchema(), name)
    else:
        print('OPENING DATABASE')
        return  db.AAPDatabase(name)

def dbDumpTable(storage: AAPStorage, table: str):
    DatabaseDumper(storage.database).DumpTable(table)
def dbDumpTables(storage: AAPStorage, tables: list[str]):
    DatabaseDumper(storage.database).DumpTables(tables)

BEDRIJVEN = ['promo','cheapo','promo Drom','campina','vreesland','fail',]
def create_bedrijven(storage: AAPStorage):
    print('--- Creating bedrijven ---')
    for bn in BEDRIJVEN: 
        storage.create_bedrijf(Bedrijf(bn))
    storage.commit()
    dbDumpTable(storage, 'BEDRIJVEN')

def test_bedrijven(storage: AAPStorage):
    print('--- Testing bedrijven ---')
    storage.update_bedrijf(Bedrijf('Bloody Mary', id=3))
    storage.commit()
    b = storage.read_bedrijf(2)
    print('BEDRIJF 2: ', b)
    storage.delete_bedrijf(b.id)
    storage.create_bedrijf(Bedrijf('beate uhse'))
    storage.commit()
    dbDumpTable(storage, 'BEDRIJVEN')


FILES = [{'filename':'jezusredt.htm', 'timestamp': datetime.strptime('2-3-1957 10:11:12', FileInfo.DATETIME_FORMAT), 'filetype': FileType.MAIL_HTM},
    {'filename':'jezusredtniet.pdf', 'timestamp': datetime.strptime('2-3-1962 9:9:9', FileInfo.DATETIME_FORMAT), 'filetype': FileType.OORDEEL_PDF},
    {'filename':'aanvraag1.pdf', 'timestamp': datetime.now(), 'filetype': FileType.AANVRAAG_PDF},
    {'filename':'aanvraag2.pdf', 'timestamp': datetime.now(), 'filetype': FileType.AANVRAAG_PDF},
    {'filename':'jezusredt.docx', 'timestamp': datetime.now(), 'filetype': FileType.OORDEEL_DOCX},
    {'filename':'jezusredt.pdf', 'timestamp': datetime.now(), 'filetype': FileType.OORDEEL_PDF},
    {'filename':'aanvraag4.pdf', 'timestamp': datetime.now(), 'filetype': FileType.AANVRAAG_PDF},
    {'filename':'aanvraag3.pdf', 'timestamp': datetime.now(), 'filetype': FileType.AANVRAAG_PDF},
]
def get_files(filename):
    for fs in FILES:
        if fs["filename"] == filename:
            return FileInfo(fs['filename'], fs['timestamp'], fs['filetype'])
    return None

def create_files(storage: AAPStorage):
    print('--- Creating files ---')
    for fs in FILES:
        storage.create_fileinfo(get_files(fs["filename"]))
    storage.commit()
    dbDumpTable(storage, 'FILES')

def test_files(storage: AAPStorage):
    print('--- Testing files ---')
    f = storage.read_fileinfo('jezusredtniet.pdf')
    print('gelezen: ', f)
    f.timestamp = datetime.now()
    print(' modified: ', f)
    storage.update_fileinfo(f)
    storage.commit()
    dbDumpTable(storage, 'FILES')
    storage.delete_fileinfo(f.filename)
    storage.commit()
    dbDumpTable(storage, 'FILES')
STUDENTEN=[    {'naam':'Erik de Noorman', 'studnr':'123456', 'tel':'06-07-08-09-10', 'email':'erik@noot.mies.com'},
    {'naam':'Erica de Zuurvrouw', 'studnr':'123458', 'tel':'16-17-18-19-20', 'email':'zuur@noot.mies.com'},
    {'naam':'Dop Bylan', 'studnr':'972834', 'tel':'+1(0)96-17-18-19-20', 'email':'dop.bylan@memail.com'},
    {'naam':'ProtoPlasma', 'studnr':'123459', 'tel':'96-17-18-19-20', 'email':'plasma@vuur.mies.com'},
    {'naam':'Zwerica Zwanepoel', 'studnr':'423459', 'tel':'86-87-18-19-20', 'email':'zwerica@vuur.mies.com'},
]
def get_student(studnr):
    for stud in STUDENTEN:
        if stud["studnr"] == studnr:
            return StudentInfo(stud['naam'], stud['studnr'], stud['tel'], stud['email'])
    return None

def create_studenten(storage: AAPStorage):
    print('--- Creating studenten ---')
    for stud in STUDENTEN:
        storage.create_student(get_student(stud['studnr']))
    storage.commit()
    dbDumpTable(storage, 'STUDENTEN')

def test_studenten(storage: AAPStorage):
    print('--- Testing studenten ---')
    s = storage.read_student('123456')
    print('gelezen: ', s)
    s.email = 'erik@shotmail.stom'
    storage.update_student(s)
    storage.delete_student('972834')
    storage.commit()
    dbDumpTable(storage, 'STUDENTEN')
    return StudentInfo()
AANVRAGEN = [
    { 'fileinfo':get_files('aanvraag1.pdf'), 'student': get_student('423459'), 'bedrijf': Bedrijf('campina'), 'date': '11-11-2022', 'titel':'De lippen van Amalia', 'beoordeling': AanvraagBeoordeling.ONVOLDOENDE, 'status':AanvraagStatus.GRADED},
    { 'fileinfo':get_files('aanvraag2.pdf'), 'student': get_student('123458'), 'bedrijf': Bedrijf('campina'), 'date': '13-11-2022', 'titel':'De handen van Amalia', 'beoordeling': AanvraagBeoordeling.VOLDOENDE, 'status':AanvraagStatus.GRADED},
    { 'fileinfo':get_files('aanvraag3.pdf'), 'student': get_student('123456'), 'bedrijf': Bedrijf('cheapo'), 'date': '15-11-2022', 'titel':'De benen van Amalia'},
    { 'fileinfo':get_files('aanvraag4.pdf'), 'student': get_student('123459'), 'bedrijf': Bedrijf('fail'), 'date': '18-11-2022', 'titel':'De voeten van Amalia'},]

def create_aanvragen(storage: AAPStorage):
    print('--- Creating aanvragen ---')
    for aanvraag in AANVRAGEN:
        storage.create_aanvraag(AanvraagInfo(aanvraag['fileinfo'], aanvraag['student'], aanvraag['bedrijf'], aanvraag['date'], aanvraag['titel'], 
                            aanvraag.get('beoordeling', AanvraagBeoordeling.TE_BEOORDELEN), aanvraag.get('status', AanvraagStatus.INITIAL)))

    newFile = FileInfo('Nieuwe Haring.pdf', datetime.now(),FileType.AANVRAAG_PDF)
    newBedrijf = Bedrijf('Bax Bier')
    newStudent = StudentInfo('Lisanne Dollmer', '333333', '021-234456', 'san2954969@hotmail.com')
    storage.create_aanvraag(AanvraagInfo(newFile, newStudent, newBedrijf, '12-12-2022', 'Automatisering van de bierleverantie'))
    storage.commit()
    dbDumpTable(storage, 'AANVRAGEN')

def test_aanvragen(storage: AAPStorage):
    print('--- Testing aanvragen ---')
    aanvraag = storage.read_aanvraag(1)
    print(aanvraag)
    aanvraag = storage.read_aanvraag(3)
    print(aanvraag)
    aanvraag.titel='de onderbroek'
    print(f'{aanvraag.id} {aanvraag}')
    storage.update_aanvraag(aanvraag)
    print(f'modified: {storage.read_aanvraag(aanvraag.id)}   ')
    storage.delete_aanvraag(aanvraag.id)
    storage.commit()
    dbDumpTable(storage, 'AANVRAGEN')

def create_all(storage:AAPStorage):
    create_studenten(storage)
    create_bedrijven(storage)
    create_files(storage)
    create_aanvragen(storage)
    

jimi = r'C:\repos\aap\testdata\2. Beoordeling afstudeeropdracht (1).pdf'

recreate = len(sys.argv) > 1  and sys.argv[1].lower() == '/r'
database = create_database(DBNAME, recreate)
storage = AAPStorage(database)
if recreate:
    create_all(storage)
DatabaseDumper(database).DumpTables([])
if not recreate:
    # test_bedrijven(storage)
    # test_files(storage)
    # test_studenten(storage)
    test_aanvragen(storage)    
    # for aanvraag in storage.read_aanvragen(lambda a: a.status==AanvraagStatus.INITIAL):
    #     print(aanvraag)
    import_aanvraag(jimi, storage)
    import_aanvraag(jimi, storage)
    report_aanvragen_XLS(storage, 'texy.xlsx')#, lambda a: a.status == AanvraagStatus.GRADED)
    dbDumpTables(storage, ['FILES', 'AANVRAGEN'])
database.close()


