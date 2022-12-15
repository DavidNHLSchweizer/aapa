
from pathlib import Path
from data.aanvraag_info import AUTOTIMESTAMP, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from data.aanvraag_processor import AanvraagProcessor
from files.word_reader import WordReader
from data.storage import AAPStorage


VOLDOENDE = 'voldoende'
def is_voldoende(beoordeling: str)->bool:
    return beoordeling.lower() == VOLDOENDE

class BeoordelingOordeelReader(WordReader):
    #read grade from the file
    def read_data(self)->str:
        def read_cell_value(table, rownr, colnr)->str:
            try:
                cell_text = table.Cell(Row=rownr,Column=colnr).Range.Text
                # returned cell_text for some reason ends with both an 0x0d and a 0x07
                return cell_text[:-2]
            except Exception as E:
                print(E)
                grade = ''
            return ''
        # ROW_STUDENT = 1
        ROW_GRADE   = 5
        COL_VALUES  = 2
        if (table := self.__find_table()):
            return (read_cell_value(table, ROW_GRADE,COL_VALUES))
        else:
            return ''
    def __find_table(self):
        if self.document.Tables.Count > 0:
            return self.document.Tables(1)
        else:
            return None

class BeoordelingenReaderProcessor(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.reader = BeoordelingOordeelReader()
    def file_is_modified(self, aanvraag: AanvraagInfo, docpath):
        registered_version = aanvraag.files.get_timestamp(FileType.OORDEEL_DOCX)
        current_version = FileInfo(docpath, filetype=FileType.OORDEEL_DOCX)
        return current_version.timestamp != registered_version
    def __process_grade(self, aanvraag: AanvraagInfo, docpath: str, grade:str):
        match(grade.lower()):
            case 'voldoende': self.__process_voldoende(aanvraag, docpath)
            case 'onvoldoende': self.__process_onvoldoende(aanvraag, docpath)
            case _: raise Exception(f'unexpected grade {grade} from file {docpath}...{aanvraag}')        
    def __process_voldoende(self, aanvraag, docpath):
        aanvraag.status = AanvraagStatus.GRADED
        new_fileinfo = FileInfo(docpath, timestamp=AUTOTIMESTAMP, filetype=FileType.OORDEEL_DOCX)
        aanvraag.files.set_info()
    def process_file(self, aanvraag: AanvraagInfo, docpath: str):
        try:
            self.reader.open_document(docpath)
            grade = self.reader.read_data()
            print(f'{aanvraag}: {grade}')
            self.__process_grade(aanvraag, docpath, grade)
        finally:
            self.reader.close()

    def process(self, filter_func = None):
        for aanvraag in self.filtered_aanvragen(filter_func):
            if aanvraag.status != AanvraagStatus.NEEDS_GRADING:
                continue            
            docpath = aanvraag.files.get_filename(FileType.OORDEEL_DOCX)
            if self.file_is_modified(aanvraag, docpath):
                self.process_file(aanvraag, docpath)

        # self.merger.merge_documents(self.filtered_aanvragen(filter_func))

def read_beoordelingen_files(storage: AAPStorage, filter_func = None):
    print('***** start reading *****')
    BP=BeoordelingenReaderProcessor(storage)
    BP.process(filter_func)
    # file_creator = BeoordelingenFileCreator(storage, template_doc, output_directory)
    # file_creator.process(filter_func) 