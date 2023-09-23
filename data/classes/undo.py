from __future__ import annotations
from dataclasses import dataclass
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.process_log import ProcessLog
from general.singleton import Singleton

@dataclass
class UndoRecipe:
    final_state: Aanvraag.Status
    final_beoordeling: Aanvraag.Beoordeling
    files_to_delete: list[File.Type] = []
    files_to_forget: list[File.Type] = []
    forget_aanvraag = False
          
class UndoRecipeFactory(Singleton):
    def create(self, activity: ProcessLog.Action)->UndoRecipe:
        match activity:
            case ProcessLog.Action.CREATE:
                return UndoRecipe(final_state=None, final_beoordeling=None, files_to_forget=[File.Type.AANVRAAG_PDF], forget_aanvraag=True) 
            case ProcessLog.Action.SCAN:
                return UndoRecipe(final_state=Aanvraag.Status.INITIAL, final_beoordeling=Aanvraag.Beoordeling.TE_BEOORDELEN, 
                                  files_to_delete=[File.Type.TO_BE_GRADED_DOCX, File.Type.COPIED_PDF, File.Type.DIFFERENCE_HTML])
                                      
            case ProcessLog.Action.MAIL:
                return UndoRecipe(final_state=Aanvraag.Status.NEEDS_GRADING, final_beoordeling=Aanvraag.Beoordeling.TE_BEOORDELEN, 
                                  files_to_delete=[File.Type.GRADED_DOCX, File.Type.GRADED_PDF])                       
            case _:
                return None
