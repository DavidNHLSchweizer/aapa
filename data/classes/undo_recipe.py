from __future__ import annotations
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.undo_logs import UndoLog
from data.classes.verslagen import Verslag
from general.singleton import Singleton
from main.options import AAPAProcessingOptions

class UndoRecipe:
    #NOTE: kan niet als dataclass wegens gedoe met mutable field lists waar het niet helderder van wordt
    def __init__(self, files_to_delete: list[File.Type] = [], files_to_forget: list[File.Type] = [], optional_files: list[File.Type] = []):
        self.files_to_delete = files_to_delete
        self.files_to_forget = files_to_forget
        self.optional_files = optional_files
        
class UndoAanvragenRecipe(UndoRecipe):
    def __init__(self, final_state: Aanvraag.Status, final_beoordeling: Aanvraag.Beoordeling, files_to_delete: list[File.Type] = [],
                 files_to_forget: list[File.Type] = [], optional_files: list[File.Type] = [],# forget_aanvraag = False, 
                 forget_invalid_files = False, delete_aanvragen = False):
        super().__init__(files_to_delete=files_to_delete, files_to_forget=files_to_forget, optional_files=optional_files)
        self.final_state = final_state
        self.final_beoordeling = final_beoordeling
        self.forget_invalid_files = forget_invalid_files
        self.delete_aanvragen = delete_aanvragen

class UndoVerslagenRecipe(UndoRecipe):
    def __init__(self, final_state: Verslag.Status, files_to_delete: list[File.Type] = [],
                 files_to_forget: list[File.Type] = [], delete_directories=False, delete_verslagen = False):
        super().__init__(files_to_delete=files_to_delete, files_to_forget=files_to_forget)
        self.final_state = final_state       
        self.delete_directories =delete_directories
        self.delete_verslagen = delete_verslagen

class UndoRecipeFactory(Singleton):
    def create(self, activity: UndoLog.Action, processing_mode: AAPAProcessingOptions.PROCESSINGMODE)->UndoRecipe:
        match processing_mode:
            case AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN:
                match activity:
                    case UndoLog.Action.INPUT:
                        return UndoAanvragenRecipe(final_state=Aanvraag.Status.DELETED, 
                                        final_beoordeling=None, 
                                        files_to_forget=[File.Type.AANVRAAG_PDF], 
                                        forget_invalid_files=True, delete_aanvragen=True) 
                    case UndoLog.Action.FORM:
                        return UndoAanvragenRecipe(final_state=Aanvraag.Status.IMPORTED_PDF, 
                                        final_beoordeling=Aanvraag.Beoordeling.TE_BEOORDELEN, 
                                        files_to_delete=[File.Type.GRADE_FORM_DOCX, File.Type.COPIED_PDF,
                                                        File.Type.DIFFERENCE_HTML], 
                                                        optional_files = [File.Type.DIFFERENCE_HTML])                                      
                    case UndoLog.Action.MAIL:
                        return UndoAanvragenRecipe(final_state=Aanvraag.Status.NEEDS_GRADING, 
                                        final_beoordeling=Aanvraag.Beoordeling.TE_BEOORDELEN, 
                                        files_to_delete=[File.Type.GRADE_FORM_PDF],
                                        files_to_forget=[])                 
                    case _:
                        return None
            case AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN:
                match activity:
                    case UndoLog.Action.INPUT:
                        return UndoVerslagenRecipe(final_state=Verslag.Status.INVALID,                                          
                                        files_to_delete=[File.Type.PVA, File.Type.ONDERZOEKS_VERSLAG, File.Type.EIND_VERSLAG, File.Type.TECHNISCH_VERSLAG], 
                                        delete_verslagen=True) 
                    case UndoLog.Action.FORM:
                        return UndoVerslagenRecipe(final_state=Verslag.Status.NEW, 
                                        files_to_delete=[File.Type.GRADE_FORM_DOCX, File.Type.GRADE_FORM_EX1_DOCX, File.Type.GRADE_FORM_EX2_DOCX, File.Type.GRADE_FORM_EX3_DOCX])
                    case _: return None                                      
