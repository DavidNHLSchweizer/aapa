from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.fileutil import file_exists, summary_string
from general.log import log_error, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.beoordeling import GradeForm, aanvraag_beoordeling

class ReadFormGradeProcessor(AanvraagProcessor):
    def must_process(self, aanvraag: Aanvraag): 
        return aanvraag.status in {Aanvraag.Status.NEEDS_GRADING} and self.file_is_modified(aanvraag, File.Type.TO_BE_GRADED_DOCX)
    def process(self, aanvraag: Aanvraag, preview=False)->bool:
        doc_path = aanvraag.files.get_filename(File.Type.TO_BE_GRADED_DOCX)
        if not file_exists(doc_path):
            log_error(f'Beoordelingsbestand {doc_path} bestaat niet.')
            return False
        with GradeForm().open_document(doc_path) as reader:
            grade_str = reader.read_grade_str()            
            if (beoordeling:=aanvraag_beoordeling(grade_str)) in {Aanvraag.Beoordeling.VOLDOENDE, Aanvraag.Beoordeling.ONVOLDOENDE}:
                aanvraag.beoordeling = beoordeling
                aanvraag.status= Aanvraag.Status.GRADED
                aanvraag.unregister_file(File.Type.TO_BE_GRADED_DOCX)
                aanvraag.register_file(doc_path, File.Type.GRADED_DOCX)
                log_print(f'Beoordeling {summary_string(aanvraag.summary(), maxlen=80)}: {beoordeling}')
                return True
            else:
                log_warning(f'Aanvraag {summary_string(aanvraag.summary(), maxlen=80)}:\n\tonverwachte beoordeling: "{grade_str}"')
                return False
