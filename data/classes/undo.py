from __future__ import annotations
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.action_log import ActionLog
from general.singleton import Singleton

class UndoRecipe:
    #NOTE: kan niet als dataclass wegens gedoe met mutable field lists waar het niet helderder van wordt
    def __init__(self, final_state: Aanvraag.Status, final_beoordeling: Aanvraag.Beoordeling, files_to_delete: list[File.Type] = [],
                 files_to_forget: list[File.Type] = [], optional_files: list[File.Type] = [], forget_aanvraag = False, forget_invalid_files = False):
        self.final_state = final_state
        self.final_beoordeling = final_beoordeling
        self.files_to_delete = files_to_delete
        self.files_to_forget = files_to_forget
        self.optional_files = optional_files
        self.forget_aanvraag = forget_aanvraag
        self.forget_invalid_files = forget_invalid_files
        
# NOG 1 dingetje: de beoordelingsfile moet niet worden verwijderd door undo van de MAIL! rest lijkt nu wel aardig te werken,

class UndoRecipeFactory(Singleton):
    def create(self, activity: ActionLog.Action)->UndoRecipe:
        match activity:
            case ActionLog.Action.SCAN:
                return UndoRecipe(final_state=Aanvraag.Status.DELETED, 
                                  final_beoordeling=None, 
                                  files_to_forget=[File.Type.AANVRAAG_PDF], forget_aanvraag=True, forget_invalid_files=True) 
            case ActionLog.Action.FORM:
                return UndoRecipe(final_state=Aanvraag.Status.IMPORTED_PDF, 
                                  final_beoordeling=Aanvraag.Beoordeling.TE_BEOORDELEN, 
                                  files_to_delete=[File.Type.GRADE_FORM_DOCX, File.Type.COPIED_PDF,
                                                   File.Type.DIFFERENCE_HTML], 
                                                   optional_files = [File.Type.DIFFERENCE_HTML])                                      
            case ActionLog.Action.MAIL:
                return UndoRecipe(final_state=Aanvraag.Status.NEEDS_GRADING, 
                                  final_beoordeling=Aanvraag.Beoordeling.TE_BEOORDELEN, 
                                  files_to_delete=[File.Type.GRADE_FORM_PDF],
                                  files_to_forget=[])                 
            case _:
                return None
