from pathlib import Path
import data.AAPdatabase as db
from data.aanvraag_info import Bedrijf
from database.dump import DatabaseDumper

DBNAME =  'AAP.DB'

recreate = True
if recreate or not Path(DBNAME).is_file():
    database = db.AAPDatabase.create_from_schema(db.AAPSchema(), 'AAP.db')
else:
    database = db.AAPDatabase(DBNAME)
dbd = DatabaseDumper(database)

bc = db.CRUD_bedrijven(database)

bc.create(Bedrijf('promo'))
bc.create(Bedrijf('cheapo'))
bc.create(Bedrijf('promo'))
bc.create(Bedrijf('campina'))
database.commit()
bc.update(Bedrijf('Bloody Mary', id=3))
database.commit()
dbd.DumpTables()


