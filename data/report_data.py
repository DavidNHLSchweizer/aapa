from enum import Enum
from pathlib import Path
import pandas as pd
from process.aanvraag_processor import AanvraagProcessor
from data.classes import AanvraagInfo
from data.storage import AAPStorage
from general.fileutil import writable_filename

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
        
class AanvraagDataXLS:   
    def __init__(self, xls_filename):
        self.xls_filename = writable_filename(xls_filename)
        self.writer:pd.ExcelWriter = self.open_xls()
    def open_xls(self):
        writer:pd.ExcelWriter = self.__init_xls(self.xls_filename)
        if writer:
            self.sheet = writer.sheets['Sheet1']
        else:
            self.sheet = None
        return writer
    def __init_xls(self, xls_filename):
        pd.DataFrame(columns=COLMAP.keys()).to_excel(xls_filename, index=False)
        return pd.ExcelWriter(self.xls_filename, engine='openpyxl', mode='a') 
    def report(self, aanvragen: list[AanvraagInfo]):
        for aanvraag in aanvragen:
            self.sheet.append(self.__to_sheet_row(aanvraag))
    def __to_sheet_row(self, aanvraag: AanvraagInfo):
        return [aanvraag.aanvraag_source_file_path().name, aanvraag.timestamp, aanvraag.student.student_name, aanvraag.student.studnr, aanvraag.student.first_name, aanvraag.student.telno, aanvraag.student.email, 
                aanvraag.datum_str, str(aanvraag.aanvraag_nr), aanvraag.bedrijf.bedrijfsnaam, aanvraag.titel, str(aanvraag.status), str(aanvraag.beoordeling)]
    def number_rows(self):
        return self.sheet.max_row
    def close(self):
        print(f'Rapport  ({self.number_rows()-1} aanvragen) geschreven naar {self.xls_filename}.')
        self.writer.close()

class AanvraagDataXLSReporter(AanvraagProcessor):
    def process(self, xls_filename: str, filter_func=None):
        reporter = AanvraagDataXLS(xls_filename)
        reporter.report(self.filtered_aanvragen(filter_func))
        reporter.close()

class AanvraagDataConsoleReporter(AanvraagProcessor):
    def process(self, filter_func=None):
        for aanvraag in self.filtered_aanvragen(filter_func):
            print(aanvraag)

def report_aanvragen_XLS(storage: AAPStorage, xls_filename: str, filter_func = None):
    AanvraagDataXLSReporter(storage).process(xls_filename, filter_func)

def report_aanvragen_console(storage: AAPStorage, filter_func = None):
    AanvraagDataConsoleReporter(storage).process(filter_func)
