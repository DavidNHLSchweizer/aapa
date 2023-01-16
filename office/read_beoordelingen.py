from contextlib import contextmanager
from data.aanvraag_info import AanvraagInfo, FileInfo, FileType
from general.log import logPrint
from office.verwerk_beoordeling import BeoordelingenProcessor, GradeInputReader, verwerk_beoordelingen
from data.storage import AAPStorage

class WordDocumentGradeReader(GradeInputReader):
    @contextmanager
    def load_aanvraag(self, aanvraag: AanvraagInfo, doc_path: str):
        with self.open_document(doc_path=doc_path) as document:
            yield document
    #read grade from the file
    def read_data(self)->str:
        def read_cell_value(table, rownr, colnr)->str:
            try:
                cell_text = table.Cell(Row=rownr,Column=colnr).Range.Text
                # returned cell_text for some reason ends with both an 0x0d and a 0x07
                return cell_text[:-2]
            except Exception as E:
                print(E)
            return ''
        ROW_GRADE   = 5
        COL_VALUES  = 2
        if (table := self.find_table(1)):
            return (read_cell_value(table, ROW_GRADE,COL_VALUES))
        else:
            return ''
    def grade(self, aanvraag: AanvraagInfo)->str:
        return self.read_data()

class BeoordelingenFromWordDocument(BeoordelingenProcessor):
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(WordDocumentGradeReader(), storage, aanvragen)
    def file_is_modified(self, aanvraag: AanvraagInfo, docpath):        
        registered_version = aanvraag.files.get_timestamp(FileType.TO_BE_GRADED_DOCX)
        current_version = FileInfo(docpath, filetype=FileType.TO_BE_GRADED_DOCX)
        return current_version.timestamp != registered_version
    def must_process(self, aanvraag, docpath): 
        return self.file_is_modified(aanvraag, docpath)

def read_beoordelingen_from_files(storage: AAPStorage, filter_func = None, preview=False):
    logPrint('--- Verwerken beoordeelde formulieren...')
    verwerk_beoordelingen(BeoordelingenFromWordDocument(storage), storage=storage, filter_func = filter_func, preview=preview)
    logPrint('--- Einde verwerken beoordeelde formulieren.')
