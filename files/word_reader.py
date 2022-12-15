from pathlib import Path
import win32com.client as win32, pywintypes

def path_with_suffix(filename, suffix):
    path = Path(filename)
    return path.parent.joinpath(f'{path.stem}{suffix}')

wdFormatFilteredHTML = 10
wdFormatPDF = 17
class WordReader:
    def __init__(self, doc_path=None):
        self.word= win32.Dispatch('word.application')
        self.word.visible = 0
        self.doc_path = doc_path
        self._document = None
    @property 
    def document(self):
        return self._document
    # @document.setter
    # def document(self, value):
    #     self._document = self.open_document(str(doc_path)) if doc_path else None
    def open_document(self, doc_path):
        if self.document:
            self.close()
        self.word.Documents.Open(doc_path, ReadOnly=-1)
        self._document = self.word.ActiveDocument
    def _save_as(self, file_format, suffix):
        save_name = str(path_with_suffix(self.doc_path, suffix))
        self.document.SaveAs(save_name, FileFormat=file_format)
        return save_name
    def save_as_pdf(self):
        self._save_as(wdFormatPDF, '.pdf')
    def save_as_htm(self):
        self._save_as(wdFormatFilteredHTML, '.htm')
    def close(self):
        try:
            if self.document:
                self.document.Close()
            self._document = None
        except pywintypes.com_error as E:
            pass 
        # the COM system sometimes seems to close itself when not necessary, 
        # 'The object invoked has disconnected from its clients.'
        # it seems harmless to ignore this.
        #TODO: research and solve
    def __del__(self):
        self.close()
            