from pathlib import Path
from data.classes.aanvragen import AanvraagInfo, AanvraagStatus
from data.classes.files import FileType
from general.fileutil import path_with_suffix, summary_string
from general.log import log_error, log_print
from general.preview import pva
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.word_processor import Word2PdfConvertor

class ArchiveGradedFileProcessor(AanvraagProcessor):
    def must_process(self, aanvraag: AanvraagInfo): 
        return aanvraag.status in {AanvraagStatus.GRADED} #and self.file_is_modified(aanvraag, FileType.TO_BE_GRADED_DOCX)        
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        aanvraag_path = aanvraag.aanvraag_source_file_name().parent
        graded_file = Path(aanvraag.files.get_filename(FileType.GRADED_DOCX))
        pdf_file_name = str(path_with_suffix(aanvraag_path.joinpath(graded_file.name), '.pdf').resolve())
        try:            
            log_print(f'\tFeedback file {pva(preview, "aan te maken", "aanmaken")} en archiveren:\n\t{summary_string(pdf_file_name, maxlen=96)}.')
            if not preview:
                Word2PdfConvertor().convert(str(graded_file), pdf_file_name)
        except Exception as E:
            log_error(f'Fout bij archiveren {summary_string(pdf_file_name, 80)}:\n\t{E}')
            return False
        aanvraag.register_file(pdf_file_name, FileType.GRADED_PDF)
        aanvraag.status = AanvraagStatus.ARCHIVED
        if not preview:
            log_print(f'\tFeedback file aangemaakt en gearchiveerd')
        return True
        
