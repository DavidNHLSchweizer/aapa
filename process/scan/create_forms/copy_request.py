from pathlib import Path
import shutil
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.fileutil import file_exists, summary_string
from general.log import log_print
from general.preview import pva
from process.general.aanvraag_processor import AanvraagProcessor


class CopyAanvraagProcessor(AanvraagProcessor):
    def __init__(self,  output_directory: str):
        self.output_directory = Path(output_directory)
        super().__init__(entry_states={Aanvraag.Status.IMPORTED_PDF, Aanvraag.Status.NEEDS_GRADING})
    @staticmethod
    def _get_copy_filename(output_directory:Path, aanvraag: Aanvraag, copy_filename: str = None):
        rootname = f'Aanvraag {aanvraag.student.full_name} ({aanvraag.student.stud_nr})-{aanvraag.aanvraag_nr}' if not copy_filename else copy_filename
        copy_filename = output_directory.joinpath(f'{rootname}.pdf')
        if file_exists(str(copy_filename)):
            return CopyAanvraagProcessor._get_copy_filename(output_directory, aanvraag, rootname+'(copy)')
        else:
            return copy_filename
    def must_process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        already_there = (filename := aanvraag.files.get_filename(File.Type.COPIED_PDF)) and file_exists(filename)
        if already_there:
            return False
        elif preview:
            return not file_exists(CopyAanvraagProcessor._get_copy_filename(self.output_directory, aanvraag))
        else: 
            return True
    def process(self, aanvraag: Aanvraag, preview=False, **kwdargs)->bool:
        aanvraag_filename = aanvraag.aanvraag_source_file_name()
        copy_filename = CopyAanvraagProcessor._get_copy_filename(self.output_directory, aanvraag)
        if not preview:
            shutil.copy2(aanvraag_filename, copy_filename)
        aanvraag.register_file(copy_filename, File.Type.COPIED_PDF)
        log_print(f'\t{pva(preview, "Te kopiëren", "Gekopiëerd")}: aanvraag {summary_string(aanvraag_filename)} to\n\t\t{summary_string(copy_filename)}.')      
        return True

