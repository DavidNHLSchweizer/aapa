
from data.classes.files import File
from data.classes.undo_logs import UndoLog
from main.log import log_error, log_info, log_print
from main.options import AAPAProcessingOptions
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.general.verslag_pipeline import VerslagenPipeline
from process.undo.undo_aanvragen_processor import UndoAanvragenProcessor, process_delete_aanvragen
from process.undo.undo_verslagen_processor import UndoVerslagenProcessor, process_delete_verslagen
from storage.aapa_storage import AAPAStorage
from storage.queries.undo_logs import UndoLogQueries

def __delete_file(file: File, storage: AAPAStorage):
    log_print(f'\t\t{File.display_file(file.filename)}')
    storage.delete('files', file)

def _process_forget_invalid_files(undo_log: UndoLog, storage: AAPAStorage):
    if not undo_log.files:
        return        
    log_info(f'\tVerwijderen overige gevonden pdf-bestanden uit database:', to_console=True)
    for file in undo_log.files:
        __delete_file(file, storage)
    undo_log.clear_files()
    storage.update('undo_logs', undo_log)
    storage.commit()
    log_info(f'\tEinde verwijderen overige gevonden pdf-bestanden uit database.', to_console=True)

def _process_forget_files(files_to_forget: list[File], storage: AAPAStorage):
    log_info(f'\tVerwijderen te vergeten bestanden uit database:', to_console=True)
    for file in files_to_forget:
        __delete_file(file, storage)
    storage.commit()
    log_info(f'\tEinde verwijderen te vergeten bestanden uit database.', to_console=True)

def undo_last_aanvragen(storage: AAPAStorage, preview=False)->int:    
    log_info('--- Ongedaan maken verwerking aanvragen ...', True)
    queries : UndoLogQueries = storage.queries('undo_logs')
    if not (undo_log:=queries.last_undo_log(AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN)):
        log_error(f'Kan ongedaan te maken acties niet laden uit database.')
        return None
    nr_aanvragen = undo_log.nr_aanvragen 
    processor = UndoAanvragenProcessor(undo_log)
       
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
        process_delete_aanvragen(aanvragen_to_delete, storage)
    if processor.files_to_forget:
        _process_forget_files(processor.files_to_forget, storage)
    if processor.recipe.forget_invalid_files:
        _process_forget_invalid_files(undo_log, storage)
    return result

def undo_last_verslagen(storage: AAPAStorage, preview=False)->int:    
    log_info('--- Ongedaan maken verwerking verslagen ...', True)
    queries : UndoLogQueries = storage.queries('undo_logs')
    if not (undo_log:=queries.last_undo_log(AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN)):
        log_error(f'Kan ongedaan te maken acties niet laden uit database.')
        return None
    nr_verslagen = undo_log.nr_verslagen
    processor = UndoVerslagenProcessor(undo_log)
       
    # remember which aanvragen to delete, lists in undolog will be cleared by processing
    verslagen_to_delete = undo_log.verslagen.copy() if processor.recipe.delete_verslagen else None 
        
    pipeline = VerslagenPipeline('Ongedaan maken verwerking verslagen', processor, storage, 
                                  UndoLog.Action.UNDO, can_undo=False, verslagen=undo_log.verslagen.copy()) 
                #copy is needed here because processing will remove verslagen from the undo_log.verslagen list
                #at the end of the individual process call, so we cannot use the same list to determine the verslagen to 
                # process by the pipeline
    result = pipeline.process(preview=preview) 
    if result == nr_verslagen:
        undo_log.can_undo = False
    storage.update('undo_logs', undo_log)
    storage.commit()
    log_info('--- Einde ongedaan maken verwerking verslagen.', True)
    if verslagen_to_delete:
        process_delete_verslagen(verslagen_to_delete, storage)
    if processor.files_to_forget:
        _process_forget_files(processor.files_to_forget, storage)
    return result
