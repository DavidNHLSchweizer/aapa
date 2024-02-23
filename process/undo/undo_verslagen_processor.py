from data.classes.undo_logs import UndoLog
from data.classes.files import File
from data.classes.undo_recipe import UndoRecipeFactory, UndoVerslagenRecipe
from data.classes.verslagen import Verslag
from main.options import AAPAProcessingOptions
from process.general.verslag_processor import VerslagProcessor
from storage.aapa_storage import AAPAStorage
from general.fileutil import delete_if_exists, file_exists
from main.log import log_info, log_print, log_warning
from process.general.verslag_processor import VerslagProcessor
class UndoException(Exception): pass

#"serious" issues (waarschijnlijk):
#verwijderen files moet ze ook verwijderen uit mijlpaal_directories
#dit zou ook moeten gelden voor aanvragen, overigens.

class UndoVerslagenProcessor(VerslagProcessor):
    def __init__(self, undo_log: UndoLog):
        self.recipe: UndoVerslagenRecipe = UndoRecipeFactory().create(undo_log.action, processing_mode=AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN)
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
    def _process_files_to_delete(self, verslag: Verslag, preview=False):
        if not self.recipe.files_to_delete:
            return
        log_info(f'\tVerwijderen aangemaakte bestanden:', to_console=True)
        for filetype in self.recipe.files_to_delete:
            self.__delete_file(verslag.files.get_file(filetype), preview=preview)
            verslag.unregister_file(filetype) # als het goed is wordt de file daarmee ook uit de database geschrapt! TODO Hier moet ik nog iets mee!
        log_info(f'\tEinde verwijderen aangemaakte bestanden', to_console=True)
    def _process_files_to_forget(self, verslag: Verslag, preview=False):
        if not self.recipe.files_to_forget or self.recipe.files_to_forget == []:
            return
        log_info(f'\tBepalen te verwijderen bestanden uit database:', to_console=True)
        for filetype in self.recipe.files_to_forget:
            log_print(f'\t\t{File.display_file(verslag.files.get_filename(filetype))}')
            self.files_to_forget.append(verslag.files.get_file(filetype))
            verslag.unregister_file(filetype) # als het goed is wordt de file daarmee ook uit de database geschrapt! TODO Hier moet ik nog iets mee!
        log_info(f'\tEinde bepalen te verwijderen bestanden uit database', to_console=True)
    def process(self, verslag: Verslag, preview = False, **kwargs)->bool:
        # if self.recipe.forget_invalid_files:
        #     self.undo_log.clear_invalid_files()    
        #     self.recipe.forget_invalid_files = False #need only once
        log_info(f'Ongedaan maken voor verslag {verslag.summary()}.', to_console=True)
        self._process_files_to_delete(verslag, preview)
        self.undo_log.remove(verslag)
        log_info(f'Einde ongedaan maken voor verslag {verslag.summary()}.', to_console=True)
        # if self.recipe.final_state == Verslag.Status.DELETED:
        #     log_info(f'Verwijdering verslag {verslag.summary()} is voltooid.', to_console=True)
        return True

def process_delete_verslagen(verslagen: list[Verslag], storage: AAPAStorage):
    if not verslagen:
        return        
    log_info(f'\tVerwijderen verslagen uit database:', to_console=True)
    for verslag in verslagen:
        log_print(f'\t\t{verslag.summary()}')
        storage.delete('verslagen', verslag)
    storage.commit()
    log_info(f'\tEinde verwijderen verslagen uit database.', to_console=True)
