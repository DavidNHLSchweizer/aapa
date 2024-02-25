from data.classes.aanvragen import Aanvraag
from data.classes.undo_logs import UndoLog
from data.classes.files import File
from data.classes.undo_recipe import UndoAanvragenRecipe, UndoRecipe, UndoRecipeFactory
from main.options import AAPAProcessingOptions
from storage.aapa_storage import AAPAStorage
from storage.queries.undo_logs import UndoLogsQueries
from general.fileutil import delete_if_exists, file_exists
from main.log import log_error, log_info, log_print, log_warning
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.general.aanvraag_processor import AanvraagProcessor
class UndoException(Exception): pass

class UndoAanvragenProcessor(AanvraagProcessor):
    def __init__(self, undo_log: UndoLog):
        self.recipe: UndoAanvragenRecipe = UndoRecipeFactory().create(undo_log.action, processing_mode=AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN)
        self.files_to_forget = []
        self.undo_log = undo_log
        super().__init__(exit_state = self.recipe.final_state, description='Ongedaan maken')
    def __delete_file(self, file: File, preview=False):
        if file is None:
            return
        if file.filename is None or not file_exists(file.filename):            
            if not file.filetype in self.recipe.optional_files:
                log_warning(f'\t\tBestand {File.display_file(file.filename)} ({file.filetype}) niet aangemaakt of niet gevonden.')
            return   
        log_print(f'\t\t{File.display_file(file.filename)}')
        self.files_to_forget.append(file)
        if not preview:
            delete_if_exists(file.filename)
    def _process_files_to_delete(self, aanvraag: Aanvraag, preview=False):
        if not self.recipe.files_to_delete:
            return
        log_info(f'\tVerwijderen aangemaakte bestanden:', to_console=True)
        for filetype in self.recipe.files_to_delete:
            self.__delete_file(aanvraag.files.get_file(filetype), preview=preview)
            aanvraag.unregister_file(filetype) # als het goed is wordt de file daarmee ook uit de database geschrapt!
        log_info(f'\tEinde verwijderen aangemaakte bestanden', to_console=True)
    def _process_files_to_forget(self, aanvraag: Aanvraag, preview=False):
        if not self.recipe.files_to_forget or self.recipe.files_to_forget == []:
            return
        log_info(f'\tBepalen te verwijderen bestanden uit database:', to_console=True)
        for filetype in self.recipe.files_to_forget:
            log_print(f'\t\t{File.display_file(aanvraag.files.get_filename(filetype))}')
            self.files_to_forget.append(aanvraag.files.get_file(filetype))
            aanvraag.unregister_file(filetype) 
        log_info(f'\tEinde bepalen te verwijderen bestanden uit database', to_console=True)
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        # if self.recipe.forget_invalid_files:
        #     self.undo_log.clear_invalid_files()    
        #     self.recipe.forget_invalid_files = False #need only once
        log_info(f'Ongedaan maken voor aanvraag {aanvraag.summary()}.', to_console=True)
        self._process_files_to_delete(aanvraag, preview)
        self._process_files_to_forget(aanvraag, preview)
        if self.recipe.final_beoordeling and self.recipe.final_beoordeling != aanvraag.beoordeling:
            aanvraag.beoordeling = self.recipe.final_beoordeling
        self.undo_log.remove(aanvraag)
        log_info(f'Einde ongedaan maken voor aanvraag {aanvraag.summary()}.', to_console=True)
        # if self.recipe.final_state == Aanvraag.Status.DELETED:
        #     log_info(f'Verwijdering aanvraag {aanvraag.summary()} is voltooid.', to_console=True)
        return True

def process_delete_aanvragen(aanvragen: list[Aanvraag], storage: AAPAStorage):
    if not aanvragen:
        return        
    log_info(f'\tVerwijderen aanvragen uit database:', to_console=True)
    for aanvraag in aanvragen:
        log_print(f'\t\t{aanvraag.summary()}')
        storage.delete('aanvragen', aanvraag)
    storage.commit()
    log_info(f'\tEinde verwijderen aanvragen uit database.', to_console=True)

