from contextlib import contextmanager
from enum import Enum
import pandas as pd
from data.classes.action_log import ActionLog
from general.log import log_error, log_print
from process.general.aanvraag_processor import AanvraagProcessor
from data.classes.aanvragen import Aanvraag
from data.storage import AAPAStorage
from general.fileutil import writable_filename
from general.config import config
from process.general.pipeline import ProcessingPipeline

DEFAULTFILENAME = 'aanvragen.xlsx'
def init_config():
    config.init('report', 'filename', DEFAULTFILENAME)
init_config()

class COLMAP(Enum):
    FILENAME:0 
    TIMESTAMP:1 
    STUDENT:2
    STUDENTNR: 3 
    VOORNAAM: 4 
    TELEFOONNUMMER: 5 
    EMAIL:6
    DATUM:7 
    VERSIE: 8   
    BEDRIJF:9
    TITEL:10
    STATUS:11
    BEOORDELING:12
    @staticmethod
    def keys():
        return [name.lower() for name, _ in COLMAP.__annotations__.items()]
    @staticmethod
    def value(value_name):
        value_name = value_name.upper()
        for name, val in COLMAP.__annotations__.items():
            if name == value_name:
                return val
        return None

class AanvraagXLSReporter(AanvraagProcessor):
    def __init__(self):
        self.writer = None
        self.sheet = None
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
        pd.DataFrame(columns=COLMAP.keys()).to_excel(xls_filename, index=False)
        return pd.ExcelWriter(xls_filename, engine='openpyxl', mode='a') 
    def process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        if self.sheet:
            self.sheet.append(self.__to_sheet_row(aanvraag))
            return True
        return False
    def __to_sheet_row(self, aanvraag: Aanvraag):
        return [aanvraag.aanvraag_source_file_name().name, aanvraag.timestamp, aanvraag.student.full_name, aanvraag.student.stud_nr, aanvraag.student.first_name, aanvraag.student.tel_nr, aanvraag.student.email, 
                aanvraag.datum_str, str(aanvraag.aanvraag_nr), aanvraag.bedrijf.name, aanvraag.titel, str(aanvraag.status), str(aanvraag.beoordeling)]
    
def report_aanvragen_XLS(storage: AAPAStorage, xls_filename: str, filter_func = None):
    xls_filename = writable_filename(xls_filename)
    reporter = AanvraagXLSReporter()
    pipeline = ProcessingPipeline('Maken XLS rapportage', reporter, storage, activity=ActionLog.Action.NOLOG, can_undo=False)
    with reporter.open_xls(xls_filename):
        n_reported = pipeline.process()
    log_print(f'Rapport ({n_reported} aanvragen) geschreven naar {xls_filename}.')
