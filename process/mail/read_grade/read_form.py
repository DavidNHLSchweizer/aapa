from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.studenten import Student
from general.fileutil import file_exists
from main.log import log_error, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.beoordeling import GradeForm, aanvraag_beoordeling

class ReadFormGradeProcessor(AanvraagProcessor):
    def __init__(self):
        super().__init__(entry_states={Aanvraag.Status.NEEDS_GRADING}, 
                         exit_state=Aanvraag.Status.GRADED,
                         description='Lees beoordeling'
                         )
    def file_is_modified(self, aanvraag: Aanvraag, filetype: File.Type):        
        filename = aanvraag.files.get_filename(filetype)
        registered_timestamp = aanvraag.files.get_timestamp(filetype)
        current_timestamp = File.get_timestamp(filename)
        registered_digest  = aanvraag.files.get_digest(filetype)
        current_digest = File.get_digest(filename)        
        return current_timestamp != registered_timestamp or current_digest != registered_digest
        #TODO: Er lijkt wel eens wat mis te gaan bij het opslaan van de digest, maar misschien valt dat mee. Gevolgen lijken mee te vallen.
    def must_process(self, aanvraag: Aanvraag, preview=False): 
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
                log_print(f'Beoordeling {aanvraag.summary(maxlen=80)}: {beoordeling}')
                if beoordeling == Aanvraag.Beoordeling.VOLDOENDE:
                    aanvraag.student.status = Student.Status.BEZIG
                return True
            else:
                log_warning(f'Aanvraag {aanvraag.summary(maxlen=80)}:\n\tonverwachte beoordeling: "{grade_str}"')
                return False
