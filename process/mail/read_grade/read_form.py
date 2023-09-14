from data.classes import AUTOTIMESTAMP, AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import file_exists, summary_string
from general.log import log_error, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.beoordeling import GradeForm, aanvraag_beoordeling

class ReadFormGradeProcessor(AanvraagProcessor):
    def must_process(self, aanvraag: AanvraagInfo): 
        return aanvraag.status in {AanvraagStatus.NEEDS_GRADING} and self.file_is_modified(aanvraag, FileType.TO_BE_GRADED_DOCX)
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        doc_path = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
        if not file_exists(doc_path):
            log_error(f'Beoordelingsbestand {doc_path} bestaat niet.')
            return False
        with GradeForm().open_document(doc_path) as reader:
            grade_str = reader.read_grade_str()            
            if (beoordeling:=aanvraag_beoordeling(grade_str)) in {AanvraagBeoordeling.VOLDOENDE, AanvraagBeoordeling.ONVOLDOENDE}:
                aanvraag.beoordeling = beoordeling
                aanvraag.status= AanvraagStatus.GRADED
                aanvraag.files.reset_info(FileType.TO_BE_GRADED_DOCX)
                aanvraag.files.set_info(FileInfo(doc_path, timestamp=AUTOTIMESTAMP, filetype=FileType.GRADED_DOCX, aanvraag_id=aanvraag.id))
                log_print(f'Beoordeling {summary_string(aanvraag.summary(), maxlen=80)}: {beoordeling}')
                return True
            else:
                log_warning(f'Aanvraag {summary_string(aanvraag.summary(), maxlen=80)}:\n\tonverwachte beoordeling: "{grade_str}"')
                return False
