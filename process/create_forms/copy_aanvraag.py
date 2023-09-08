from pathlib import Path
import shutil
from data.classes import AanvraagInfo, AanvraagStatus, FileType
from general.fileutil import file_exists, summary_string
from general.log import log_print
from process.new_aanvraag_processor import NewAanvraagProcessor


class CopyAanvraagProcessor(NewAanvraagProcessor):
    def __init__(self,  output_directory: str):
        self.output_directory = Path(output_directory)
    @staticmethod
    def _get_copy_filename(output_directory:Path, aanvraag: AanvraagInfo, copy_filename: str = None):
        rootname = f'Aanvraag {aanvraag.student.student_name} ({aanvraag.student.studnr})-{aanvraag.aanvraag_nr}' if not copy_filename else copy_filename
        copy_filename = output_directory.joinpath(f'{rootname}.pdf')
        if file_exists(str(copy_filename)):
            return CopyAanvraagProcessor._get_copy_filename(output_directory, aanvraag, rootname+'(copy)')
        else:
            return copy_filename
    def must_process(self, aanvraag: AanvraagInfo, preview=False, **kwargs)->bool:
        if not aanvraag.status in [AanvraagStatus.NEEDS_GRADING]:
            return False
        else:
            already_there = (filename := aanvraag.files.get_filename(FileType.COPIED_PDF)) and file_exists(filename)
            if already_there:
                return False
            elif preview:
                return not file_exists(CopyAanvraagProcessor._get_copy_filename(self.output_directory, aanvraag))
            else: 
                return True
    def process(self, aanvraag: AanvraagInfo, preview=False, **kwdargs)->bool:
        aanvraag_filename = aanvraag.aanvraag_source_file_name()
        copy_filename = CopyAanvraagProcessor._get_copy_filename(self.output_directory, aanvraag)
        if not preview:
            shutil.copy2(aanvraag_filename, copy_filename)
        kopied = 'Te kopiëren' if preview else 'Gekopiëerd'
        log_print(f'\t{kopied}: aanvraag {summary_string(aanvraag_filename)} to {summary_string(copy_filename)}.')
        aanvraag.files.set_filename(FileType.COPIED_PDF, copy_filename)
        return True

