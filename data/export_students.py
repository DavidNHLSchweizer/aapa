from contextlib import contextmanager
from enum import Enum
from multiprocessing.process import BaseProcess
import pandas as pd
from data.classes.undo_logs import UndoLog
from general.deep_attr import deep_attr_main_part, get_deep_attr
from general.log import log_error, log_print
from process.general.aanvraag_processor import AanvraagProcessor
from data.classes.aanvragen import Aanvraag
from data.storage.aapa_storage import AAPAStorage
from general.fileutil import writable_filename
from general.config import config
from process.general.pipeline import AanvragenPipeline

DEFAULTFILENAME = 'aanvragen.xlsx'
def init_config():
    config.init('report', 'filename', DEFAULTFILENAME)
init_config()


class ExcelMapper:
    class Flags(Enum):
        NONE = 0
        FUNCTION = 1
        SUBATTRIB = 2
        STR  = 3
    ExcelAanvraagMap = {'student_full_name': {'header': 'student', 'column': 0, 'attrib': 'student.full_name', 'flags': Flags.SUBATTRIB},
                        'student_stud_nr': {'header': 'studentnr', 'column': 4, 'attrib': 'student.stud_nr','flags': Flags.SUBATTRIB},
                        'student_first_name': {'header': 'voornaam', 'column': 5, 'attrib': 'student.first_name','flags': Flags.SUBATTRIB},
                        'student_tel_nr': {'header': 'telefoonnr', 'column': 6, 'attrib': 'student.tel_nr','flags': Flags.SUBATTRIB},
                        'student_email': {'header': 'email', 'column': 7, 'attrib': 'student.email','flags': Flags.SUBATTRIB},
                       }
    def __init__(self):
        self._aanvraag = None
    def get_attrib(self, aanvraag: Aanvraag, key: str)->str:
        if not (entry:=ExcelMapper.ExcelAanvraagMap[key]):
            return ''
        match entry['flags']:
            case ExcelMapper.Flags.NONE: return getattr(aanvraag, entry['attrib'], None)
            case ExcelMapper.Flags.STR: return str(getattr(aanvraag, entry['attrib'], None))
            case ExcelMapper.Flags.FUNCTION: 
                if (func :=  getattr(aanvraag, entry['attrib'], None)):
                    return func()
                return ''
            case ExcelMapper.Flags.SUBATTRIB:
                return get_deep_attr(aanvraag, entry['attrib'], '')
            case _: return ''
    def sheet_row(self, aanvraag: Aanvraag)->list[str]:
        return [self.get_attrib(aanvraag, key) for key in ExcelMapper.ExcelAanvraagMap.keys()]
  
class StudentXLSReporter(BaseProcess):
    def __init__(self):
        self.writer = None
        self.sheet = None
        self.mapper = ExcelMapper()
        super().__init__(description='Maken XLS rapportage')
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
        pd.DataFrame(columns=[entry['header'] for entry in ExcelMapper.ExcelAanvraagMap.values()]).to_excel(xls_filename, index=False)        
        return pd.ExcelWriter(xls_filename, engine='openpyxl', mode='a') 
    def process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        if self.sheet:
            self.sheet.append(self.mapper.sheet_row(aanvraag))
            return True
        return False
             
def report_aanvragen_XLS(storage: AAPAStorage, xls_filename: str, filter_func = None):
    xls_filename = writable_filename(xls_filename)
    reporter = StudentXLSReporter()
    pipeline = AanvragenPipeline('Maken XLS rapportage', reporter, storage, activity=UndoLog.Action.NOLOG, can_undo=False)
    with reporter.open_xls(xls_filename):
        n_reported = pipeline.process()
    log_print(f'Rapport ({n_reported} aanvragen) geschreven naar {xls_filename}.')
