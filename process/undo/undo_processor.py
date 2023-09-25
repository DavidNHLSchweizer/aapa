import os
from data.classes.aanvragen import Aanvraag
from data.classes.process_log import ProcessLog
from data.classes.files import File
from data.classes.undo import UndoRecipe, UndoRecipeFactory
from data.storage import AAPAStorage
from general.fileutil import delete_if_exists, file_exists, summary_string
from general.log import log_debug, log_error, log_info, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor, AanvraagProcessorBase, AanvragenProcessor

class UndoException(Exception): pass

class StateLogProcessor(AanvraagProcessorBase):
    def state_change(self, log: ProcessLog, storage: AAPAStorage, preview = False, **kwargs)->bool: 
        return False

class UndoRecipeProcessor(AanvraagProcessor):
    def __init__(self, process_log: ProcessLog):
        self.recipe: UndoRecipe = UndoRecipeFactory().create(process_log.action)
        self.ids_to_delete = []
        self.process_log = process_log
        super().__init__(exit_state = self.recipe.final_state)
    def __delete_file(self, filetype: File.Type, filename: str, preview=False):
        if (filename is None or not file_exists(filename)):            
            if not filetype in self.recipe.optional_files:
                log_warning(f'\t\tBestand {summary_string(filename)} ({filetype}) niet aangemaakt of niet gevonden.')
            return   
        log_print(f'\t\t{summary_string(filename)}')
        if not preview:
            delete_if_exists(filename)
    def _process_files_to_delete(self, aanvraag: Aanvraag, preview=False):
        if not self.recipe.files_to_delete:
            return
        log_info(f'\tVerwijderen aangemaakte bestanden:', to_console=True)
        for filetype in self.recipe.files_to_delete:
            filename = aanvraag.files.get_filename(filetype)
            self.__delete_file(filetype, filename, preview=preview)
            aanvraag.unregister_file(filetype) # als het goed is wordt de file daarmee ook uit de database geschrapt!
        log_info(f'\tEinde verwijderen aangemaakte bestanden', to_console=True)
    def _process_files_to_forget(self, aanvraag: Aanvraag, preview=False):
        if not self.recipe.files_to_forget:
            return
        log_info(f'\tVerwijderen bestanden uit database:', to_console=True)
        for filetype in self.recipe.files_to_forget:
            log_print(f'\t\t{summary_string(aanvraag.files.get_filename(filetype))}')
            aanvraag.unregister_file(filetype) 
        log_info(f'\tEinde verwijderen bestanden uit database', to_console=True)
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        log_info(f'Ongedaan maken voor aanvraag {aanvraag.summary()}.', to_console=True)
        self._process_files_to_delete(aanvraag, preview)
        self._process_files_to_forget(aanvraag, preview)
        if self.recipe.final_beoordeling and self.recipe.final_beoordeling != aanvraag.beoordeling:
            aanvraag.beoordeling = self.recipe.final_beoordeling
        log_info(f'Einde ongedaan maken voor aanvraag {aanvraag.summary()}.', to_console=True)
        if self.recipe.final_state == Aanvraag.Status.DELETED:
            log_info(f'Verwijdering aanvraag {aanvraag.summary()} is voltooid.', to_console=True)
        return True

def undo_last(storage: AAPAStorage, preview=False)->int:    
    log_info('--- Ongedaan maken verwerking aanvragen ...', True)
    if not (process_log:=storage.process_log.find_log()):
        log_error(f'Kan ongedaan te maken acties niet laden uit database.')
        return 0
    nr_aanvragen = process_log.nr_aanvragen #NOTE als aanvragen worden verwijderd verwijderen ze ook uit de process_log 
    processor = AanvragenProcessor('Ongedaan maken verwerking aanvragen', UndoRecipeProcessor(process_log), storage, ProcessLog.Action.REVERT, aanvragen=process_log.aanvragen)
    result = processor.process_aanvragen(preview=preview) 
    if result == nr_aanvragen:
        process_log.rolled_back = True
        storage.process_log.update(process_log)
        storage.commit()
    log_info('--- Einde ongedaan maken verwerking aanvragen.', True)
    return result

