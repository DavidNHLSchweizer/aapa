import pandas as pd
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagInfo
from data.storage import AAPStorage
from general.fileutil import writable_filename

COLMAP = {'timestamp':0, 'student':1, 'studentnr':2, 'voornaam':3, 'telefoonnummer':4, 'email':5, 'datum':6, 'versie':7, 'bedrijf':8, 'titel':9, 'status':10, 'beoordeling':11}
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
        return [aanvraag.fileinfo.timestamp, aanvraag.student.student_name, aanvraag.student.studnr, aanvraag.student.first_name, aanvraag.student.telno, aanvraag.student.email, 
                aanvraag.datum_str, str(aanvraag.versie), aanvraag.bedrijf.bedrijfsnaam, aanvraag.titel, str(aanvraag.status), str(aanvraag.beoordeling)]
    def number_rows(self):
        return self.sheet.max_row
    def close(self):
        print(f'Wrote report ({self.number_rows()-1} aanvragen) to {self.xls_filename}.')
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
