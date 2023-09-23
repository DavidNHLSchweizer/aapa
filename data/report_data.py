from contextlib import contextmanager
from enum import Enum
import pandas as pd
from data.classes.process_log import ProcessLog
from general.log import log_error, log_print
from process.general.aanvraag_processor import AanvraagProcessor, AanvragenProcessor
from data.classes.aanvragen import Aanvraag
from data.storage import AAPAStorage
from general.fileutil import writable_filename
from general.config import config

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
    def process(self, aanvraag: Aanvraag, preview=False, sheet=None, **kwargs)->bool:
        sheet.append(self.__to_sheet_row(aanvraag))
        return True
    def __to_sheet_row(self, aanvraag: Aanvraag):
        return [aanvraag.aanvraag_source_file_name().name, aanvraag.timestamp, aanvraag.student.full_name, aanvraag.student.stud_nr, aanvraag.student.first_name, aanvraag.student.tel_nr, aanvraag.student.email, 
                aanvraag.datum_str, str(aanvraag.aanvraag_nr), aanvraag.bedrijf.name, aanvraag.titel, str(aanvraag.status), str(aanvraag.beoordeling)]

class AanvragenXLSReporter(AanvragenProcessor):       
    def __init__(self, storage: AAPAStorage):
        super().__init__('Maken XLS rapportage', AanvraagXLSReporter(), storage, ProcessLog.Action.NOLOG)
        self.writer = None
        self.sheet = None
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
    def process_aanvragen(self, preview=False, filter_func=None, xls_filename: str = 'aanvragen.xlsx', **kwargs) -> int: 
        result = 0
        with self.open_xls(xls_filename):
            try:
                result = super().process_aanvragen(False, filter_func, sheet = self.sheet, **kwargs)
            except Exception as E:
                log_error(f'Fout bij schrijven Excel-bestand {xls_filename}:\n\t{E}')
                result = None
        return result
    
def report_aanvragen_XLS(storage: AAPAStorage, xls_filename: str, filter_func = None):
    xls_filename = writable_filename(xls_filename)
    if (result := AanvragenXLSReporter(storage).process_aanvragen(preview=False, filter_func=filter_func, xls_filename=xls_filename)) is not None:
        log_print(f'Rapport ({result} aanvragen) geschreven naar {xls_filename}.')

#TODO: Dit eventueel aanpassen, is niet meer nodig denk ik
# class AanvraagDataConsoleReporter(AanvragenProcessor):
#     def process(self, filter_func=None):
#         for aanvraag in self.filtered_aanvragen(filter_func):
#             log_print(aanvraag)

# def report_aanvragen_console(storage: AAPStorage, filter_func = None):
#     AanvraagDataConsoleReporter(storage).process(filter_func)
