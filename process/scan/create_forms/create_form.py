from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.log import log_error, log_info, log_print
from general.fileutil import file_exists
from mailmerge import MailMerge
from general.preview import pva
from process.general.aanvraag_processor import AanvraagProcessor

class MailMergeException(Exception): pass

class FormCreator(AanvraagProcessor):
    def __init__(self, template_doc: str, output_directory: str):
        self.output_directory = Path(output_directory)
        if not file_exists(template_doc):
            raise MailMergeException(f'kan template {template_doc} niet vinden.')
        self.template_doc = template_doc
        super().__init__(entry_states={Aanvraag.Status.IMPORTED_PDF}, 
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
        return f'Beoordeling aanvraag {aanvraag.student} ({aanvraag.bedrijf.name})-{aanvraag.aanvraag_nr}.docx'
    def __merge_document(self, aanvraag: Aanvraag, preview = False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.merge_document(self.template_doc, output_filename, filename=aanvraag.aanvraag_source_file_name().name, timestamp=aanvraag.timestamp_str(), 
                        student=aanvraag.student.full_name,bedrijf=aanvraag.bedrijf.name,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr), 
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
        aanvraag.register_file(doc_path, File.Type.GRADE_FORM_DOCX)
        return True