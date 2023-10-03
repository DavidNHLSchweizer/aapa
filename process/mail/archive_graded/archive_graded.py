from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.storage import AAPAStorage
from general.fileutil import path_with_suffix, summary_string
from general.log import log_error, log_print, log_warning
from general.preview import pva
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.word_processor import Word2PdfConvertor

class ArchiveGradedFileProcessor(AanvraagProcessor):
    def __init__(self, storage: AAPAStorage):
        super().__init__(entry_states={Aanvraag.Status.GRADED}, 
                         exit_state=Aanvraag.Status.ARCHIVED, 
                         description='Archiveer beoordeling')
        self.storage = storage
    def process(self, aanvraag: Aanvraag, preview=False)->bool:
        aanvraag_path = aanvraag.aanvraag_source_file_name().parent
        graded_file = Path(aanvraag.files.get_filename(File.Type.GRADE_FORM_DOCX))
        pdf_file_name = str(path_with_suffix(aanvraag_path.joinpath(graded_file.name), '.pdf').resolve())
        if self.storage.files.is_known_invalid(pdf_file_name):
            log_warning(f'Bestand {summary_string(pdf_file_name, maxlen=96)} is al bekend in database.\n\tWordt overschreven door nieuw bestand.')
        try:            
            log_print(f'\tFeedback file {pva(preview, "aan te maken", "aanmaken")} en archiveren:\n\t{summary_string(pdf_file_name, maxlen=96)}.')
            if not preview:
                Word2PdfConvertor().convert(str(graded_file), pdf_file_name)
        except Exception as E:
            log_error(f'Fout bij archiveren {summary_string(pdf_file_name, 80)}:\n\t{E}')
            return False
        aanvraag.register_file(pdf_file_name, File.Type.GRADE_FORM_PDF)
        if not preview:
            log_print(f'\tFeedback file aangemaakt en gearchiveerd')
        return True
        
