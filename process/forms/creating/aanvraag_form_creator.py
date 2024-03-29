from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.general.const import MijlpaalType
from data.classes.files import File
from main.log import log_error, log_exception, log_print
from general.fileutil import file_exists, safe_file_name
from mailmerge import MailMerge
from process.general.preview import pva
from general.timeutil import TSC
from process.general.aanvraag_processor import AanvraagProcessor

class MailMergeException(Exception): pass

class AanvraagFormCreator(AanvraagProcessor):
    def __init__(self, template_doc: str, output_directory: str):
        self.output_directory = Path(output_directory)
        if not file_exists(template_doc):
            log_exception(f'kan template {template_doc} niet vinden.', MailMergeException)
        self.template_doc = template_doc
        super().__init__(entry_states={Aanvraag.Status.IMPORTED_PDF,Aanvraag.Status.IMPORTED_XLS}, 
                         exit_state=Aanvraag.Status.NEEDS_GRADING,
                         description='Aanmaken beoordelingsformulier')
    def merge_document(self, template_doc: str, output_file_name: str, **kwds)->str:
        preview = kwds.pop('preview', False)
        try:
            full_output_name = self.output_directory.joinpath(output_file_name)
            document = MailMerge(template_doc)
            if not preview:
                document.merge(**kwds)
                document.write(full_output_name)
            return full_output_name.resolve()
        except Exception as E:
            log_error(f'Error merging document (template:{template_doc}) to {full_output_name}: {E}')
            return None
    def __get_output_filename(self, aanvraag: Aanvraag):
        safe_user_part = safe_file_name(f'{aanvraag.student} ({aanvraag.bedrijf.name})-{aanvraag.versie}')
        return f'Beoordeling aanvraag {safe_user_part}.docx'
    def __merge_document(self, aanvraag: Aanvraag, preview = False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.merge_document(self.template_doc, output_filename, filename=aanvraag.aanvraag_source_file_path().name, 
                                   timestamp=TSC.timestamp_to_str(aanvraag.timestamp), 
                        student=aanvraag.student.full_name,bedrijf=aanvraag.bedrijf.name,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.kans), 
                        preview=preview)
    def must_process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        if not preview:
            filename = aanvraag.files.get_filename(File.Type.GRADE_FORM_DOCX)
            if filename != None:
                return not file_exists(filename)                
            else:
                return True
        else:
            filename = self.output_directory.joinpath(self.__get_output_filename(aanvraag))
            return not file_exists(filename)
    def process(self, aanvraag: Aanvraag, preview=False, **kwdargs)->bool:
        doc_path = self.__merge_document(aanvraag, preview=preview)
        log_print(f'{aanvraag}\n\tFormulier {pva(preview, "aanmaken", "aangemaakt")}: {Path(doc_path).name}.')
        aanvraag.register_file(doc_path, File.Type.GRADE_FORM_DOCX, MijlpaalType.AANVRAAG)
        return True