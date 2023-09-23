from __future__ import annotations
from dataclasses import dataclass
from data.classes.aanvragen import AanvraagStatus, AanvraagBeoordeling
from data.classes.files import FileType
from data.classes.process_log import ProcessLog
from general.singleton import Singleton

@dataclass
class UndoRecipe:
    final_state: AanvraagStatus
    final_beoordeling: AanvraagBeoordeling
    files_to_delete: list[FileType] = []
    files_to_forget: list[FileType] = []
    forget_aanvraag = False
          
class UndoRecipeFactory(Singleton):
    def create(self, activity: ProcessLog.Action)->UndoRecipe:
        match activity:
            case ProcessLog.Action.CREATE:
                return UndoRecipe(final_state=None, final_beoordeling=None, files_to_forget=[FileType.AANVRAAG_PDF], forget_aanvraag=True) 
            case ProcessLog.Action.SCAN:
                return UndoRecipe(final_state=AanvraagStatus.INITIAL, final_beoordeling=AanvraagBeoordeling.TE_BEOORDELEN, 
                                  files_to_delete=[FileType.TO_BE_GRADED_DOCX, FileType.COPIED_PDF, FileType.DIFFERENCE_HTML])
                                      
            case ProcessLog.Action.MAIL:
                return UndoRecipe(AanvraagStatus=AanvraagStatus.NEEDS_GRADING, final_beoordeling=AanvraagBeoordeling.TE_BEOORDELEN, 
                                  files_to_delete=[FileType.GRADED_DOCX, FileType.GRADED_PDF])
                       
            case _:
                return None
