
from pathlib import Path
from aanvraag_info import AanvraagInfo, AanvraagStatus
from aanvraag_processor import AanvraagProcessor
from files.word_reader import WordReader
from storage import AAPStorage


VOLDOENDE = 'voldoende'
def is_voldoende(beoordeling: str)->bool:
    return beoordeling.lower() == VOLDOENDE

class BeoordelingOordeelReader(WordReader):
    #read student and grade from the file
    def read_data(self)->tuple[str,str]:
        def read_cell_value(table, rownr, colnr)->str:
            try:
                cell_text = table.Cell(Row=rownr,Column=colnr).Range.Text
                # returned cell_text for some reason ends with both an 0x0d and a 0x07
                return cell_text[:-2]
            except Exception as E:
                print(E)
                grade = ''
            return ''
        ROW_STUDENT = 1
        ROW_GRADE   = 5
        COL_VALUES  = 2
        if (table := self.__find_table()):
            return (read_cell_value(table, ROW_STUDENT, COL_VALUES), read_cell_value(table, ROW_GRADE,COL_VALUES))
        else:
            return ('','')
    def __find_table(self):
        if self.document.Tables.Count > 0:
            return self.document.Tables(1)
        else:
            return None

class BeoordelingenReaderProcessor(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.reader = BeoordelingOordeelReader()
    def process(self, filter_func = None):
        for aanvraag in self.filtered_aanvragen(filter_func):
            if aanvraag.status != AanvraagStatus.NEEDS_GRADING:
                continue
            docpath = self.__find_docpath(aanvraag, )
        self.merger.merge_documents(self.filtered_aanvragen(filter_func))
    def __find_docpath(self, aanvraag):
        file = self.storage.find_fileinfo()
        OORDEEL_DOCX
def create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None):
    file_creator = BeoordelingenFileCreator(storage, template_doc, output_directory)
    file_creator.process(filter_func)