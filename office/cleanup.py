from pathlib import Path
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagInfo, AanvraagStatus, FileType
from general.log import logInfo, logPrint
from data.storage import AAPStorage
from general.preview import Preview

class CleanupTempFilesProcessor(AanvraagProcessor):
    def __remove_file(self,aanvraag: AanvraagInfo, filename:Path, filetype:FileType):
        filename.unlink(True)
        aanvraag.files.reset_info(filetype)
        self.storage.delete_fileinfo(str(filename))
        logPrint(f'Verwijderd: {filename}')
        aanvraag.status = AanvraagStatus.READY
        self.storage.update_aanvraag(aanvraag)
        self.storage.commit()
    def __process_files_for_aanvraag(self, aanvraag: AanvraagInfo, filetypes: list[FileType], preview=False):
        logInfo(f'start cleanup for {str(aanvraag)}')
        for filename,filetype in zip([Path(aanvraag.files.get_filename(ft)) for ft in filetypes], filetypes):
            if preview:
                print(f'\tte verwijderen: {filename} [{str(filetype)}]')
            else:
                self.__remove_file(aanvraag, filename, filetype)
        logInfo(f'end cleanup for {str(aanvraag)}')
    def process_files(self, aanvraag: AanvraagInfo, preview=False):
        logPrint(f'Opruimen {aanvraag}')
        self.__process_files_for_aanvraag(aanvraag, [FileType.GRADED_DOCX, FileType.MAIL_DOCX, FileType.MAIL_HTM], preview=preview)
    def process(self, filter_func = None, preview=False):
        for aanvraag in self.filtered_aanvragen(filter_func):
            if aanvraag.status != AanvraagStatus.MAIL_READY:
                continue            
            self.process_files(aanvraag,preview=preview)

def cleanup_files(storage: AAPStorage, filter_func = None, preview=False):
    with Preview(preview, storage, 'clean'):
        logPrint('--- Opschonen tijdelijke of onnodige bestanden...')
        cleaner = CleanupTempFilesProcessor(storage)
        cleaner.process(filter_func, preview=preview)
        logPrint('--- Einde opschonen tijdelijke of onnodige bestanden.')
