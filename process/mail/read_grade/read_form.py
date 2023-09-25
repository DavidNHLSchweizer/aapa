from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.fileutil import file_exists, summary_string
from general.log import log_error, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.beoordeling import GradeForm, aanvraag_beoordeling

class ReadFormGradeProcessor(AanvraagProcessor):
    def __init__(self):
        super().__init__(entry_states={Aanvraag.Status.NEEDS_GRADING}, exit_state=Aanvraag.Status.GRADED)
    def must_process(self, aanvraag: Aanvraag): 
        return self.file_is_modified(aanvraag, File.Type.GRADE_FORM_DOCX)
    def process(self, aanvraag: Aanvraag, preview=False)->bool:
        doc_path = aanvraag.files.get_filename(File.Type.GRADE_FORM_DOCX)
        if not file_exists(doc_path):
            log_error(f'Beoordelingsbestand {doc_path} bestaat niet.')
            return False
        with GradeForm().open_document(doc_path) as reader:
            grade_str = reader.read_grade_str()            
            if (beoordeling:=aanvraag_beoordeling(grade_str)) in {Aanvraag.Beoordeling.VOLDOENDE, Aanvraag.Beoordeling.ONVOLDOENDE}:
                aanvraag.beoordeling = beoordeling
                # aanvraag.unregister_file(File.Type.GRADE_FORM_DOCX)
                # aanvraag.register_file(doc_path, File.Type.GRADED_DOCX)
                log_print(f'Beoordeling {summary_string(aanvraag.summary(), maxlen=80)}: {beoordeling}')
                return True
            else:
                log_warning(f'Aanvraag {summary_string(aanvraag.summary(), maxlen=80)}:\n\tonverwachte beoordeling: "{grade_str}"')
                return False
