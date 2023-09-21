import os
from data.classes import AanvraagInfo
from data.state_log import ProcessLog, StateChangeFactory
from data.storage import AAPStorage
from general.fileutil import file_exists, summary_string
from general.log import log_error, log_info, log_print, log_warning
from process.general.aanvraag_processor import AanvraagProcessor, AanvraagProcessorBase, AanvragenProcessor

class RevertException(Exception): pass

class StateLogProcessor(AanvraagProcessorBase):
    def process_log(self, log: ProcessLog, storage: AAPStorage, preview = False, **kwargs)->bool: 
        return False

class AanvraagRevertProcessor(AanvraagProcessor):
    def __init__(self, activity: ProcessLog.Action):
        super().__init__()
        self._state_log = StateChangeFactory().create(activity)
    def process(self, aanvraag: AanvraagInfo, preview = False, **kwargs)->bool:
        log_info(f'Terugdraaien aanvraag {aanvraag.summary()}. Status is {aanvraag.status}')
        log_print(f'\tVerwijderen nieuwe bestanden.')
        if not aanvraag.status in self._state_log._final_states:
            raise RevertException(f'Status aanvraag {aanvraag.summary()} niet in een van de verwachte toestanden')
        for filetype in self._state_log._created_file_types:
            if not (filename := aanvraag.files.get_filename(filetype)) and not file_exists(filename):
                log_warning(f'\t\tBestand {summary_string(filename)} ({filetype}) niet aangemaakt of niet gevonden.')
                continue
            log_print(f'\t\t{summary_string(filename)}')
            if not preview:
                os.unlink(filename)
            aanvraag.unregister_file(filetype) # als het goed is wordt de file nu ook uit de database geschrapt!
        aanvraag.status = self._state_log.initial_state
        aanvraag.beoordeling = self._state_log.initial_beoordeling
        log_info(f'{aanvraag.summary()} teruggedraaid. Status is nu: {aanvraag.status}')
        return True

def revert_log(storage: AAPStorage, preview=False)->int:
    log_info('--- Terugdraaien verwerking aanvragen ...', True)
    if not (process_log:=storage.process_log.find_log()):
        log_error(f'Kan terug te draaien aanvragen niet laden uit database ')
        return 0
    print(process_log)
    processor = AanvragenProcessor('Terugdraaien verwerking aanvragen', AanvraagRevertProcessor(process_log.action), storage, ProcessLog.Action.REVERT, aanvragen=process_log.aanvragen)
    result = processor.process_aanvragen(preview=preview) 
    if result == process_log.nr_aanvragen:
        process_log.rolled_back = True
        storage.process_log.update(process_log)
        storage.commit()
    log_info('--- Einde terugdraaien verwerking aanvragen.')
    return result

