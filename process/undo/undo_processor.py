from data.classes.aanvragen import Aanvraag
from data.classes.undo_logs import UndoLog
from data.classes.files import File
from data.classes.undo import UndoRecipe, UndoRecipeFactory
from storage.aapa_storage import AAPAStorage
from storage.queries.undo_logs import UndoLogQueries
from general.fileutil import delete_if_exists, file_exists, summary_string
from main.log import log_error, log_info, log_print, log_warning
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.general.aanvraag_processor import AanvraagProcessor
class UndoException(Exception): pass

class UndoRecipeProcessor(AanvraagProcessor):
    def __init__(self, undo_log: UndoLog):
        self.recipe: UndoRecipe = UndoRecipeFactory().create(undo_log.action)
        self.files_to_forget = []
        self.undo_log = undo_log
        super().__init__(exit_state = self.recipe.final_state, description='Ongedaan maken')
    def __delete_file(self, file: File, preview=False):
        if file is None:
            return
        if file.filename is None or not file_exists(file.filename):            
            if not file.filetype in self.recipe.optional_files:
                log_warning(f'\t\tBestand {summary_string(file.filename)} ({file.filetype}) niet aangemaakt of niet gevonden.')
            return   
        log_print(f'\t\t{summary_string(file.filename)}')
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
            log_print(f'\t\t{summary_string(aanvraag.files.get_filename(filetype))}')
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

def _process_delete_aanvragen(aanvragen: list[Aanvraag], storage: AAPAStorage):
    if not aanvragen:
        return        
    log_info(f'\tVerwijderen aanvragen uit database:', to_console=True)
    for aanvraag in aanvragen:
        log_print(f'\t\t{aanvraag.summary()}')
        storage.delete('aanvragen', aanvraag)
    storage.commit()
    log_info(f'\tEinde verwijderen aanvragen uit database.', to_console=True)

def __delete_file(file: File, storage: AAPAStorage):
    log_print(f'\t\t{summary_string(file.filename, maxlen=90, initial=16)}')
    storage.delete('files', file)

def _process_forget_invalid_files(undo_log: UndoLog, storage: AAPAStorage):
    if not undo_log.invalid_files:
        return        
    log_info(f'\tVerwijderen overige gevonden pdf-bestanden uit database:', to_console=True)
    for file in undo_log.invalid_files:
        __delete_file(file, storage)
    undo_log.clear_invalid_files()
    storage.update('undo_logs', undo_log)
    storage.commit()
    log_info(f'\tEinde verwijderen overige gevonden pdf-bestanden uit database.', to_console=True)

def _process_forget_files(files_to_forget: list[File], storage: AAPAStorage):
    log_info(f'\tVerwijderen te vergeten bestanden uit database:', to_console=True)
    for file in files_to_forget:
        __delete_file(file, storage)
    storage.commit()
    log_info(f'\tEinde verwijderen te vergeten bestanden uit database.', to_console=True)

def undo_last(storage: AAPAStorage, preview=False)->int:    
    log_info('--- Ongedaan maken verwerking aanvragen ...', True)
    queries : UndoLogQueries = storage.queries('undo_logs')
    if not (undo_log:=queries.last_undo_log()):
        log_error(f'Kan ongedaan te maken acties niet laden uit database.')
        return None
    nr_aanvragen = undo_log.nr_aanvragen 
    processor = UndoRecipeProcessor(undo_log)
       
    # remember which aanvragen to delete, lists in undolog will be cleared by processing
    aanvragen_to_delete = undo_log.aanvragen.copy() if processor.recipe.delete_aanvragen else None 
        
    pipeline = AanvragenPipeline('Ongedaan maken verwerking aanvragen', processor, storage, 
                                  UndoLog.Action.UNDO, can_undo=False, aanvragen=undo_log.aanvragen.copy()) 
                #copy is needed here because processing will remove aanvragen from the undo_log.aanvragen list
                #at the end of the individual process call, so we cannot use the same list to determine the aanvragen to 
                # process by the pipeline
    result = pipeline.process(preview=preview) 
    if result == nr_aanvragen:
        undo_log.can_undo = False
    storage.update('undo_logs', undo_log)
    storage.commit()
    log_info('--- Einde ongedaan maken verwerking aanvragen.', True)
    if aanvragen_to_delete:
        _process_delete_aanvragen(aanvragen_to_delete, storage)
    if processor.files_to_forget:
        _process_forget_files(processor.files_to_forget, storage)
    if processor.recipe.forget_invalid_files:
        _process_forget_invalid_files(undo_log, storage)
    return result

