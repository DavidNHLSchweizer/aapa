from data.classes.aanvragen import Aanvraag
from data.classes.action_log import ActionLog
from data.classes.files import File
from data.classes.undo import UndoRecipe, UndoRecipeFactory
from data.storage.aapa_storage import AAPAStorage
from general.fileutil import delete_if_exists, file_exists, summary_string
from general.log import log_debug, log_error, log_info, log_print, log_warning
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.general.aanvraag_processor import AanvraagProcessor
class UndoException(Exception): pass

class UndoRecipeProcessor(AanvraagProcessor):
    def __init__(self, action_log: ActionLog):
        self.recipe: UndoRecipe = UndoRecipeFactory().create(action_log.action)
        self.ids_to_delete = []
        self.action_log = action_log
        super().__init__(exit_state = self.recipe.final_state, description='Ongedaan maken')
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
        if not self.recipe.files_to_forget or self.recipe.files_to_forget == []:
            return
        log_info(f'\tVerwijderen bestanden uit database:', to_console=True)
        for filetype in self.recipe.files_to_forget:
            log_print(f'\t\t{summary_string(aanvraag.files.get_filename(filetype))}')
            aanvraag.unregister_file(filetype) 
        log_info(f'\tEinde verwijderen bestanden uit database', to_console=True)
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        # if self.recipe.forget_invalid_files:
        #     self.action_log.clear_invalid_files()    
        #     self.recipe.forget_invalid_files = False #need only once
        log_info(f'Ongedaan maken voor aanvraag {aanvraag.summary()}.', to_console=True)
        self._process_files_to_delete(aanvraag, preview)
        self._process_files_to_forget(aanvraag, preview)
        if self.recipe.final_beoordeling and self.recipe.final_beoordeling != aanvraag.beoordeling:
            aanvraag.beoordeling = self.recipe.final_beoordeling
        self.action_log.remove_aanvraag(aanvraag)
        log_info(f'Einde ongedaan maken voor aanvraag {aanvraag.summary()}.', to_console=True)
        # if self.recipe.final_state == Aanvraag.Status.DELETED:
        #     log_info(f'Verwijdering aanvraag {aanvraag.summary()} is voltooid.', to_console=True)
        return True

def _process_delete_aanvragen(aanvragen: list[Aanvraag], storage: AAPAStorage):
    if not aanvragen:
        return        
    log_info(f'\tVerwijderen aanvragen uit database:', to_console=True)
    for aanvraag in aanvragen:
        log_print(f'\t\t{aanvraag.summary()}')
        storage.aanvragen.delete(aanvraag.id)
    storage.commit()
    log_info(f'\tEinde verwijderen aanvragen uit database.', to_console=True)


def _process_forget_invalid_files(action_log: ActionLog, storage: AAPAStorage):
    if not action_log.invalid_files:
        return        
    log_info(f'\tVerwijderen overige gevonden pdf-bestanden uit database:', to_console=True)
    for file in action_log.invalid_files:
        log_print(f'\t\t{summary_string(file.filename, maxlen=90, initial=16)}')
        storage.files.delete(file.id)
    action_log.clear_invalid_files()
    storage.action_logs.update(action_log)
    storage.commit()
    log_info(f'\tEinde verwijderen overige gevonden pdf-bestanden uit database.', to_console=True)

def undo_last(storage: AAPAStorage, preview=False)->int:    
    log_info('--- Ongedaan maken verwerking aanvragen ...', True)
    if not (action_log:=storage.action_logs.last_action()):
        log_error(f'Kan ongedaan te maken acties niet laden uit database.')
        return 0
    nr_aanvragen = action_log.nr_aanvragen 
    processor = UndoRecipeProcessor(action_log)
       
    # remember which aanvragen to delete, lists in actionlog will be cleared by processing
    aanvragen_to_delete = action_log.aanvragen.copy() if processor.recipe.delete_aanvragen else None 
        
    pipeline = AanvragenPipeline('Ongedaan maken verwerking aanvragen', processor, storage, 
                                  ActionLog.Action.UNDO, can_undo=False, aanvragen=action_log.aanvragen.copy()) 
                #copy is needed here because processing will remove aanvragen from the action_log.aanvragen list
                #at the end of the individual process call, so we cannot use the same list to determine the aanvragen to 
                # process by the pipeline
    result = pipeline.process(preview=preview) 
    if result == nr_aanvragen:
        action_log.can_undo = False
    storage.action_logs.update(action_log)
    storage.commit()
    log_info('--- Einde ongedaan maken verwerking aanvragen.', True)
    if aanvragen_to_delete:
        _process_delete_aanvragen(aanvragen_to_delete, storage)
    if processor.recipe.forget_invalid_files:
        _process_forget_invalid_files(action_log, storage)
    return result

