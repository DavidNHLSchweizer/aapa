from pathlib import Path

from data.classes import AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import path_with_suffix, summary_string
from general.log import log_print
from general.preview import pva
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.word_processor import Word2PdfConvertor


class ArchiveGradedFileProcessor(AanvraagProcessor):
    def must_process(self, aanvraag: AanvraagInfo): 
        return aanvraag.status in {AanvraagStatus.GRADED} #and self.file_is_modified(aanvraag, FileType.TO_BE_GRADED_DOCX)        
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        aanvraag_path = aanvraag.aanvraag_source_file_name().parent
        graded_name = Path(aanvraag.files.get_filename(FileType.GRADED_DOCX)).name
        pdf_file_name = str(path_with_suffix(aanvraag_path.joinpath(graded_name), '.pdf').resolve())
        if not preview:
            Word2PdfConvertor().convert(graded_name, pdf_file_name)
        aanvraag.files.set_info(FileInfo(pdf_file_name, filetype=FileType.GRADED_PDF, aanvraag_id=aanvraag.id))
        aanvraag.status = AanvraagStatus.MAIL_READY
        log_print(f'\tFeedback file {pva(preview, "aan te maken", "aangemaakt")}:\n\t{summary_string(pdf_file_name, maxlen=96)}.')
        
