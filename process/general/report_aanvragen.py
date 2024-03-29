from contextlib import contextmanager
from enum import Enum
import pandas as pd
from data.classes.undo_logs import UndoLog
from general.deep_attr import get_deep_attr
from main.log import log_print
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.general.aanvraag_processor import AanvraagProcessor
from data.classes.aanvragen import Aanvraag
from storage.aapa_storage import AAPAStorage
from general.fileutil import writable_filename
from main.config import config

DEFAULTFILENAME = 'aanvragen.xlsx'
def init_config():
    config.init('report', 'filename', DEFAULTFILENAME)
init_config()


class ExcelAanvraagMapper:
    class Flags(Enum):
        NONE = 0
        FUNCTION = 1
        SUBATTRIB = 2
        STR  = 3
    ExcelAanvraagMap = {'id': {'header': 'ID', 'column': 0, 'attrib': 'id', 'flags': Flags.NONE},
                        'source_file_name': {'header': 'bestandsnaam', 'column': 1, 'attrib': 'source_file_name', 'flags': Flags.FUNCTION},
                        'timestamp': {'header': 'tijd', 'column': 2, 'attrib': 'timestamp','flags': Flags.NONE},
                        'full_name': {'header': 'student', 'column': 3, 'attrib': 'student.full_name', 'flags': Flags.SUBATTRIB},
                        'student_stud_nr': {'header': 'studentnr', 'column': 4, 'attrib': 'student.stud_nr','flags': Flags.SUBATTRIB},
                        'student_first_name': {'header': 'voornaam', 'column': 5, 'attrib': 'student.first_name','flags': Flags.SUBATTRIB},
                        'student_email': {'header': 'email', 'column': 7, 'attrib': 'student.email','flags': Flags.SUBATTRIB},
                        'student_datum_str': {'header': 'ingevulde datum', 'column': 8, 'attrib': 'datum_str','flags': Flags.NONE},
                        'kans': {'header': 'kans',  'column': 9, 'attrib': 'kans','flags': Flags.NONE},
                        'bedrijf': {'header': 'bedrijf', 'column': 10, 'attrib': 'bedrijf.name','flags': Flags.SUBATTRIB},
                        'titel': {'header': 'titel', 'column': 11, 'attrib': 'titel','flags': Flags.NONE},
                        'status': {'header': 'status', 'column': 12, 'attrib': 'status','flags': Flags.STR},
                        'beoordeling': {'header': 'beoordeling', 'column': 13, 'attrib': 'beoordeling','flags': Flags.STR}, 
                    }
    def __init__(self):
        self._aanvraag = None
    def get_attrib(self, aanvraag: Aanvraag, key: str)->str:
        if not (entry:=ExcelAanvraagMapper.ExcelAanvraagMap[key]):
            return ''
        match entry['flags']:
            case ExcelAanvraagMapper.Flags.NONE: return getattr(aanvraag, entry['attrib'], None)
            case ExcelAanvraagMapper.Flags.STR: return str(getattr(aanvraag, entry['attrib'], None))
            case ExcelAanvraagMapper.Flags.FUNCTION: 
                if (func :=  getattr(aanvraag, entry['attrib'], None)):
                    return func()
                return ''
            case ExcelAanvraagMapper.Flags.SUBATTRIB:
                return get_deep_attr(aanvraag, entry['attrib'], '')
            case _: return ''
    def sheet_row(self, aanvraag: Aanvraag)->list[str]:
        return [self.get_attrib(aanvraag, key) for key in ExcelAanvraagMapper.ExcelAanvraagMap.keys()]
  
class AanvraagXLSReporter(AanvraagProcessor):
    def __init__(self):
        self.writer = None
        self.sheet = None
        self.mapper = ExcelAanvraagMapper()
        super().__init__(description='Maken XLS rapportage', entry_states=Aanvraag.Status.valid_states(), read_only=True)
    @contextmanager
    def open_xls(self, xls_filename: str)->pd.ExcelWriter:
        if self.writer:
            self._close()
        self.writer:pd.ExcelWriter = self.__init_xls(xls_filename)
        if self.writer:            
            self.sheet = self.writer.sheets['Sheet1']
        else:
            self.sheet = None
        yield self.writer
        self._close()
    def _close(self):
        if self.writer:
            self.writer.close()
        self.writer = None
        self.sheet = None
    def __init_xls(self, xls_filename):
        pd.DataFrame(columns=[entry['header'] for entry in ExcelAanvraagMapper.ExcelAanvraagMap.values()]).to_excel(xls_filename, index=False)        
        return pd.ExcelWriter(xls_filename, engine='openpyxl', mode='a') 
    def process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        if self.sheet:
            self.sheet.append(self.mapper.sheet_row(aanvraag))
            return True
        return False
             
def report_aanvragen_XLS(storage: AAPAStorage, xls_filename: str, filter_func = None):
    xls_filename = writable_filename(xls_filename)
    reporter = AanvraagXLSReporter()
    pipeline = AanvragenPipeline('Maken XLS rapportage', reporter, storage, activity=UndoLog.Action.NOLOG, can_undo=False)
    with reporter.open_xls(xls_filename):
        n_reported = pipeline.process()
    log_print(f'Rapport ({n_reported} aanvragen) geschreven naar {xls_filename}.')
