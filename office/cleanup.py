from pathlib import Path
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagInfo, AanvraagStatus, FileType
from general.log import logInfo, logPrint
from data.storage import AAPStorage

class CleanupTempFilesProcessor(AanvraagProcessor):
    def __process_files_for_aanvraag(self, aanvraag: AanvraagInfo, filetypes: list[FileType]):
        logInfo(f'start cleanup for {str(aanvraag)}')
        for filename,filetype in zip([Path(aanvraag.files.get_filename(ft)) for ft in filetypes], filetypes):
            filename.unlink(True)
            aanvraag.files.reset_info(filetype)
            self.storage.delete_fileinfo(filename)
            logPrint(f'Verwijderd: {filename}')
        aanvraag.status = AanvraagStatus.READY
        self.storage.update_aanvraag(aanvraag)
        self.storage.commit()

        logInfo(f'end cleanup for {str(aanvraag)}')
    def process_files(self, aanvraag: AanvraagInfo):
        logPrint(f'Opruimen {aanvraag}')
        self.__process_files_for_aanvraag(aanvraag, [FileType.GRADED_DOCX, FileType.MAIL_DOCX, FileType.MAIL_HTM])
    def process(self, filter_func = None):
        for aanvraag in self.filtered_aanvragen(filter_func):
            if aanvraag.status != AanvraagStatus.MAIL_READY:
                continue            
            self.process_files(aanvraag)

def cleanup_files(storage: AAPStorage, filter_func = None):
    logPrint('--- Opschonen tijdelijke of onnodige bestanden...')
    cleaner = CleanupTempFilesProcessor(storage)
    cleaner.process(filter_func)
    logPrint('--- Einde opschonen tijdelijke of onnodige bestanden.')
