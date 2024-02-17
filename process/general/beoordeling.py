from data.classes.aanvragen import Aanvraag
from main.config import config, IntValueConvertor
from main.log import log_exception
from process.general.word_processor import DocxWordDocument, WordReaderException

def init_config():
    config.register('form', 'table_no', IntValueConvertor)
    config.register('form', 'table_row', IntValueConvertor)
    config.register('form', 'table_col', IntValueConvertor)
    config.init('form', 'table_no', 1)
    config.init('form', 'table_row', 6)
    config.init('form', 'table_col', 2)    
init_config()

VOLDOENDE = 'voldoende'
def is_voldoende(beoordeling: str)->bool:
    return beoordeling.lower() == VOLDOENDE

def aanvraag_beoordeling(grade: str)->Aanvraag.Beoordeling:
    match grade.split()[0].split(',')[0].lower():
        case 'voldoende':   return Aanvraag.Beoordeling.VOLDOENDE
        case 'onvoldoende': return Aanvraag.Beoordeling.ONVOLDOENDE
        case _: 
            return Aanvraag.Beoordeling.TE_BEOORDELEN

class GradeForm(DocxWordDocument):
    def __init__(self):
        super().__init__()
        self.table_nr = config.get('form', 'table_no')
        self.table_row = config.get('form', 'table_row')
        self.table_col = config.get('form', 'table_col')
    def read_grade_str(self)->str:
        if (table := self.find_table(self.table_nr)):
            return self.read_table_cell(table, self.table_row,self.table_col)
        else:
            log_exception(f'Tabel niet gevonden in document {self.doc_path}', WordReaderException)        
    def read_grade(self)->Aanvraag.Beoordeling:
        return aanvraag_beoordeling(self.read_grade_str())
    def write_grade(self, grade: Aanvraag.Beoordeling | str):
        if (table := self.find_table(self.table_nr)):
            self.write_table_cell(table, self.table_row,self.table_col, str(grade))
