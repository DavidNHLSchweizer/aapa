import os
from data.classes.aanvragen import Aanvraag
from data.classes.process_log import ProcessLog
from data.classes.files import File
from data.storage import AAPStorage
from general.fileutil import delete_if_exists, file_exists, summary_string
from general.log import log_debug, log_error, log_info, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor, AanvraagProcessorBase, AanvragenProcessor

class UndoException(Exception): pass

class StateLogProcessor(AanvraagProcessorBase):
    def state_change(self, log: ProcessLog, storage: AAPStorage, preview = False, **kwargs)->bool: 
        return False

class UndoActionProcessor(AanvraagProcessor):
    #TODO: zorgen dat de laatste stap (CREATE) het juiste resultaat heeft. Aanvraag moet worden verwijderd, aanvraagfiles uit de database maar niet uit de werkelijkheid.
    def __init__(self, activity: ProcessLog.Action):
        super().__init__()
        # self.state_change: UndoRecipeBase = UndoRecipeFactory().create(activity)
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        log_info(f'Ongedaan maken voor aanvraag {aanvraag.summary()}. Status is {aanvraag.status}')
        log_print(f'{aanvraag.summary()}\n\tVerwijderen nieuwe bestanden.')
        if not aanvraag.status in self.state_change._final_states:
            raise UndoException(f'Status aanvraag {aanvraag.summary()} niet in een van de verwachte toestanden')
        for filetype in self.state_change._created_file_types:
            filename = aanvraag.files.get_filename(filetype)
            if filename is not None and self.state_change.expected_file(filetype) and not file_exists(filename):
                log_warning(f'\t\tBestand {summary_string(filename)} ({filetype}) niet aangemaakt of niet gevonden.')
                continue           
            if self.state_change.expected_file(filetype) or file_exists(filename):
                log_print(f'\t\t{summary_string(filename)}')
                if not preview:
                    delete_if_exists(filename)
            print(f'unregistering: {filetype}')
            aanvraag.unregister_file(filetype) # als het goed is wordt de file nu ook uit de database geschrapt!
        aanvraag.status = self.state_change.initial_state
        aanvraag.beoordeling = self.state_change.initial_beoordeling
        log_info(f'{aanvraag.summary()} teruggedraaid. Status is nu: {aanvraag.status}')
        return True

def undo_last(storage: AAPStorage, preview=False)->int:
    log_info('--- Ongedaan maken verwerking aanvragen ...', True)
    if not (process_log:=storage.process_log.find_log()):
        log_error(f'Kan ongedaan te maken acties niet laden uit database.')
        return 0
    log_debug(process_log)
    processor = AanvragenProcessor('Ongedaan maken verwerking aanvragen', UndoActionProcessor(process_log.action), storage, ProcessLog.Action.REVERT, aanvragen=process_log.aanvragen)
    result = processor.process_aanvragen(preview=preview) 
    if result == process_log.nr_aanvragen:
        process_log.rolled_back = True
        storage.process_log.update(process_log)
        storage.commit()
    log_info('--- Einde terugdraaien verwerking aanvragen.')
    return result

