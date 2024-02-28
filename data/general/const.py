""" data.classes.const module: Constanten en enums voor de AAPA classes 

Voor meer info: zie data.classes.const.doc()

"""
from __future__ import annotations
from enum import Enum, IntEnum, auto
from pathlib import Path

_UNKNOWN = '!unknown'
UNKNOWN_STUDNR = 'UNKNOWN_STUDNR'

class SuffixType(Enum):
    """ real world file types. FileType is already something else. """
    UNKNOWN = auto()
    NONE    = auto()    
    DOCX    = auto()
    PDF     = auto()
    HTML    = auto()
    JSON    = auto()
    XLSX    = auto()
    @staticmethod
    def from_filename(filename: str)->SuffixType:
        match(Path(filename).suffix.lower()):
            case '.docx'|'.doc': return SuffixType.DOCX
            case '.pdf': return SuffixType.PDF
            case '.htm' | '.html': return SuffixType.HTML
            case '.json': return SuffixType.JSON
            case '.xlsx'|'.xls': return SuffixType.XLSX
            case '': return SuffixType.NONE
            case _: return SuffixType.UNKNOWN
    
class FileType(IntEnum):
    """ constanten gebruikt om verschillende filetypes aan te geven.

    Voor meer info: zie FileType.doc()

    """
    INVALID_DIR         = -4
    INVALID_DOCX        = -3
    INVALID_PDF         = -2
    UNKNOWN             = -1
    AANVRAAG_PDF        = 0
    GRADE_FORM_DOCX     = 1
    COPIED_PDF          = 2
    DIFFERENCE_HTML     = 3
    GRADE_FORM_PDF      = 5
    GRADE_FORM_EX1_DOCX = 6
    GRADE_FORM_EX2_DOCX = 7
    GRADE_FORM_EX3_DOCX = 8
    PVA                 = 9
    ONDERZOEKS_VERSLAG  = 10        
    TECHNISCH_VERSLAG   = 11       
    EIND_VERSLAG        = 12
    AANVRAAG_OTHER      = 13
    GENERAL_PDF         = 20
    GENERAL_DOCX        = 21    
    def __str__(self):
        _FT_STRS = {FileType.UNKNOWN: _UNKNOWN, 
                    FileType.INVALID_DIR: 'directory (geen verdere gegevens)',
                    FileType.INVALID_DOCX: 'docx-bestand (geen verdere gegevens)',
                    FileType.INVALID_PDF:'pdf-bestand (geen verdere gegevens)',
                    FileType.AANVRAAG_PDF: 'PDF-file (aanvraag)',  
                    FileType.GRADE_FORM_DOCX: 'Beoordelingsformulier', 
                    FileType.GRADE_FORM_PDF: 'Ingevuld beoordelingsformulier (PDF format)', 
                    FileType.COPIED_PDF: 'Kopie van PDF-file (aanvraag)',
                    FileType.DIFFERENCE_HTML: 'Verschilbestand met vorige versie aanvraag',
                    FileType.GRADE_FORM_EX1_DOCX: 'Beoordelingsformulier (examinator 1)',
                    FileType.GRADE_FORM_EX2_DOCX: 'Beoordelingsformulier (examinator 2)',
                    FileType.GRADE_FORM_EX3_DOCX: 'Beoordelingsformulier (examinator 3 of hoger)',
                    FileType.PVA: 'Plan van Aanpak',
                    FileType.ONDERZOEKS_VERSLAG: 'Onderzoeksverslag',
                    FileType.TECHNISCH_VERSLAG: 'Technisch verslag',
                    FileType.EIND_VERSLAG: 'Eindverslag',
                    FileType.AANVRAAG_OTHER: 'Aanvraag',
                    FileType.GENERAL_DOCX:'Microsoft Word bestand',
                    FileType.GENERAL_PDF:'PDF bestand'
                    }
        return _FT_STRS.get(self, _UNKNOWN)
    @staticmethod
    def is_invalid(filetype: FileType)->bool:
        return filetype in FileType.invalid_file_types()
    @staticmethod
    def valid_file_types()->set[FileType]:
        result =  {filetype for filetype in FileType if not filetype in FileType.invalid_file_types()}
        return result
    @staticmethod
    def invalid_file_types()->set[FileType]:
        return {FileType.INVALID_PDF, FileType.INVALID_DOCX}
    def default_suffix(self)->str:
        match self:
            case self.UNKNOWN: return '.unknown'
            case self.INVALID_DIR: return ''
            case self.INVALID_DOCX|self.GRADE_FORM_DOCX|self.GRADE_FORM_EX1_DOCX|self.GRADE_FORM_EX2_DOCX|self.GRADE_FORM_EX1_DOCX|self.GENERAL_DOCX:
                return '.docx'
            case self.INVALID_PDF|self.AANVRAAG_PDF|self.COPIED_PDF|self.GRADE_FORM_PDF|self.GENERAL_PDF:
                return '.pdf'
            case self.DIFFERENCE_HTML: 
                return '.html'
            case self.PVA|self.ONDERZOEKSVERSLAG|self.TECHNISCH_VERSLAG|self.EIND_VERSLAG:
                return '.pdf'
            case _: return f'.onbekend_{self}'           
    @staticmethod
    def doc()->str:
        return "\n".join([f'{ft.value:2} (FileType.{ft.name}): {str(ft)}' for ft in FileType])  

class MijlpaalType(IntEnum):
    """ constanten gebruikt om verschillende soorten "mijlpalen" aan te geven.
    
    Wordt gebruikt om verschillende types verslagen, maar ook de bijbehorende 
    student-directories te onderscheiden.

    Voor meer info: zie MijlpaalType.doc()
    
    """
    UNKNOWN             = 0
    AANVRAAG            = 1
    PVA                 = 2
    ONDERZOEKS_VERSLAG  = 3
    TECHNISCH_VERSLAG   = 4
    EIND_VERSLAG        = 5
    PRODUCT_BEOORDELING = 6
    PRESENTATIE         = 7
    EINDBEOORDELING     = 8
    AFSTUDEERZITTING    = 9
    def is_verslag(self)->bool:
        return self in {MijlpaalType.PVA,MijlpaalType.EIND_VERSLAG,MijlpaalType.ONDERZOEKS_VERSLAG,MijlpaalType.TECHNISCH_VERSLAG,MijlpaalType.PRESENTATIE,MijlpaalType.PRODUCT_BEOORDELING}
    @staticmethod
    def verslag_types()->set[MijlpaalType]:
        return {mp for mp in MijlpaalType if mp.is_verslag()}
    def default_filetype(self)->FileType:
        match self:
            case MijlpaalType.AANVRAAG: return FileType.AANVRAAG_PDF
            case MijlpaalType.PVA: return FileType.PVA
            case MijlpaalType.ONDERZOEKS_VERSLAG: return FileType.ONDERZOEKS_VERSLAG
            case MijlpaalType.TECHNISCH_VERSLAG: return FileType.TECHNISCH_VERSLAG
            case MijlpaalType.EIND_VERSLAG: return FileType.EIND_VERSLAG
            case _: return FileType.UNKNOWN
    def __str__(self):
        _MT_STRS = {MijlpaalType.UNKNOWN: '', MijlpaalType.AANVRAAG: 'aanvraag', MijlpaalType.PVA: 'plan van aanpak', 
                    MijlpaalType.ONDERZOEKS_VERSLAG: 'onderzoeksverslag', MijlpaalType.TECHNISCH_VERSLAG: 'technisch verslag',
                    MijlpaalType.EIND_VERSLAG: 'eindverslag', MijlpaalType.PRODUCT_BEOORDELING: 'productbeoordeling',
                    MijlpaalType.PRESENTATIE: 'presentatie', MijlpaalType.EINDBEOORDELING: 'eindbeoordeling', 
                    MijlpaalType.AFSTUDEERZITTING: 'afstudeerzitting' }
        return _MT_STRS.get(self, _UNKNOWN)
    def has_single_examinator(self)->bool:
        return not self in {MijlpaalType.ONDERZOEKS_VERSLAG, MijlpaalType.TECHNISCH_VERSLAG, MijlpaalType.EIND_VERSLAG }
    @staticmethod
    def doc()->str:
        return "\n".join([f'{mpt.value:2} (MijlpaalType.{mpt.name}): {str(mpt)}' for mpt in MijlpaalType])

class AanvraagStatus(IntEnum):
    """ constanten gebruikt om de processing-status van een aanvraaag aan te geven.
    
    Voor meer info: zie AanvraagStatus.doc()
        
    """
    DELETED         = -1
    NEW             = 0
    IMPORTED_PDF    = 1
    IMPORTED_XLS    = 2
    NEEDS_GRADING   = 3
    GRADED          = 4 
    ARCHIVED        = 5 
    MAIL_READY      = 6
    READY           = 7
    READY_IMPORTED  = 8
    def __str__(self):
        _AS_STRS = {AanvraagStatus.DELETED: 'verwijderd', AanvraagStatus.NEW: 'nog niet bekend', 
                    AanvraagStatus.IMPORTED_PDF: 'gelezen (PDF)',  AanvraagStatus.IMPORTED_XLS: 'geimporteerd (PDF)',
                AanvraagStatus.NEEDS_GRADING: 'te beoordelen', AanvraagStatus.GRADED: 'beoordeeld', 
                AanvraagStatus.ARCHIVED: 'gearchiveerd', AanvraagStatus.MAIL_READY: 'mail klaar voor verzending', AanvraagStatus.READY: 'geheel verwerkt', 
                AanvraagStatus.READY_IMPORTED: 'verwerkt (ingelezen via Excel)'}
        return _AS_STRS.get(self,_UNKNOWN)
    @staticmethod
    def valid_states()->set[AanvraagStatus]:
        return {status for status in AanvraagStatus} - {AanvraagStatus.DELETED}
    def active_states()->set[AanvraagStatus]:
        return AanvraagStatus.valid_states() - {AanvraagStatus.READY, AanvraagStatus.READY_IMPORTED,AanvraagStatus.MAIL_READY}
    @staticmethod
    def doc()->str:
        return "\n".join([f'{status.value:2} (AanvraagStatus.{status.name}): {str(status)}' for status in AanvraagStatus])
        
class MijlpaalStatus(IntEnum):
    """ constanten gebruikt om de processing-status van een verslag aan te geven.
    
    #TODO: het onderliggende proces is nog niet afgerond

    Voor meer info: zie MijlpaalStatus.doc()
        
    """
    NEW             = 0
    NEEDS_GRADING   = 1
    GRADED          = 2
    READY           = 3
    def __str__(self):
        _MS_STRS = {MijlpaalStatus.NEW: 'nieuw', MijlpaalStatus.NEEDS_GRADING: 'te beoordelen', MijlpaalStatus.GRADED: 'beoordeeld', 
                MijlpaalStatus.READY: 'geheel verwerkt'}
        return _MS_STRS.get(self, _UNKNOWN)
    @staticmethod
    def doc()->str:
        return "\n".join([f'{status.value:2} (MijlpaalStatus.{status.name}): {str(status)}' for status in MijlpaalStatus])

class MijlpaalBeoordeling(IntEnum):
    """ constanten gebruikt om de beoordeling van een aanvraag of een verslag aan te geven.
    
    #TODO: het onderliggende proces is voor verslagen nog niet afgerond

    Voor meer info: zie MijlpaalBeoordeling.doc()
        
    """
    TE_BEOORDELEN = 0
    ONVOLDOENDE   = 1
    VOLDOENDE     = 2
    def __str__(self):
        _MB_STRS = {MijlpaalBeoordeling.TE_BEOORDELEN: '', MijlpaalBeoordeling.ONVOLDOENDE: 'onvoldoende', MijlpaalBeoordeling.VOLDOENDE: 'voldoende'}
        return _MB_STRS.get(self,_UNKNOWN)
    @staticmethod
    def doc()->str:
        return "\n".join([f'{beoord.value:2} (MijlpaalBeoordeling.{beoord.name}): {str(beoord)}' for beoord in MijlpaalBeoordeling])

class StudentStatus(IntEnum):
    """ constanten gebruikt om de status van een student (in het afstudeertraject) aan te geven.
    
    Voor meer info: zie StudentStatus.doc()

    """
    UNKNOWN     = 0
    AANVRAAG    = 1
    BEZIG       = 2
    AFGESTUDEERD= 3 
    GESTOPT     = 10
    def __str__(self):
        STRS = {StudentStatus.UNKNOWN: 'nog niet bekend', StudentStatus.AANVRAAG: 'aanvraag gedaan',  
                StudentStatus.BEZIG: 'bezig met afstuderen', StudentStatus.AFGESTUDEERD: 'afgestudeerd', 
                StudentStatus.GESTOPT: 'gestopt'}
        return STRS[self.value]
    @staticmethod
    def doc()->str:
        return "\n".join([f'{status.value:2} (StudentStatus.{status.name}): {str(status)}' for status in StudentStatus])        
    @staticmethod
    def active_states():
        return {StudentStatus.UNKNOWN,StudentStatus.AANVRAAG,StudentStatus.BEZIG}

class StudentDirectoryStatus(IntEnum):
    """ constanten gebruikt om de status van een studentdirectory aan te geven.
    
    Voor meer info: zie StudentDirectoryStatus.doc()

    """
    UNKNOWN     = 0
    ACTIVE      = 1
    ARCHIVED    = 42 
    def __str__(self):
        STRS = {StudentDirectoryStatus.UNKNOWN: 'nog niet bekend', StudentDirectoryStatus.ACTIVE: 'actief',  
                StudentDirectoryStatus.ARCHIVED: 'gearchiveerd'}
        return STRS[self.value]
    @staticmethod
    def doc()->str:
        return "\n".join([f'{status.value:2} (StudentDirectoryStatus.{status.name}): {str(status)}' for status in StudentDirectoryStatus])        

class VerslagStatus(IntEnum):
    """ constanten gebruikt om de status van een verslag (in het afstudeertraject) aan te geven.
    
    TODO: het onderliggende proces is nog niet geimplementeerd.

    Voor meer info: zie VerslagStatus.doc()

    """
    LEGACY          = -2
    INVALID         = -1
    NEW             = 0
    NEW_MULTIPLE    = 1
    NEEDS_GRADING   = 2
    GRADED          = 3
    READY           = 4
    def __str__(self):
        STRS = {VerslagStatus.LEGACY: 'erfenis',VerslagStatus.INVALID: 'ongeldig', 
                VerslagStatus.NEW: 'nieuw', VerslagStatus.NEEDS_GRADING: 'te beoordelen', 
                VerslagStatus.NEW_MULTIPLE: 'nieuw (met bijlages)',
                VerslagStatus.GRADED: 'beoordeeld', 
                VerslagStatus.READY: 'geheel verwerkt'}
        return STRS.get(self, _UNKNOWN)
    @staticmethod
    def valid_states()->set[VerslagStatus]:
        return {status for status in VerslagStatus} - {VerslagStatus.INVALID}
    @staticmethod
    def doc()->str:
        return "\n".join([f'{status.value:2} (VerslagStatus.{status.name}): {str(status)}' for status in VerslagStatus])        

#--------------------
@staticmethod
def doc()->str:
    """ eenvoudige manier om van alle constanten te doc() af te printen.
        
        python const.py is voldoende.
    """
    return "\n----\n".join([class_type.doc() for class_type in [FileType, MijlpaalType, AanvraagStatus, MijlpaalStatus, MijlpaalBeoordeling,StudentStatus,StudentDirectoryStatus,VerslagStatus]])

if __name__ == "__main__":
    print(doc())