from __future__ import annotations
from enum import IntEnum

_UNKNOWN = '!unknown'
class FileType(IntEnum):
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
    def __str__(self):
        _FT_STRS = {FileType.UNKNOWN: '?', 
                    FileType.INVALID_DIR: 'directory (geen verdere gegevens)',
                    FileType.INVALID_DOCX|FileType.INVALID_PDF: 'bestand (geen verdere gegevens)',
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
                    FileType.AANVRAAG_OTHER: 'Aanvraag'
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

class MijlpaalType(IntEnum):
    UNKNOWN             = 0
    AANVRAAG            = 1
    PVA                 = 2
    ONDERZOEKS_VERSLAG  = 3
    TECHNISCH_VERSLAG   = 4
    EIND_VERSLAG        = 5
    PRODUCT_BEOORDELING = 6.
    PRESENTATIE         = 7
    EINDBEOORDELING     = 8
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
                    MijlpaalType.PRESENTATIE: 'presentatie', MijlpaalType.EINDBEOORDELING: 'eindbeoordeling' }
        return _MT_STRS.get(self, _UNKNOWN)
    
class AanvraagStatus(IntEnum):
    DELETED         = -1
    NEW             = 0
    IMPORTED_PDF    = 1
    NEEDS_GRADING   = 2
    GRADED          = 3
    ARCHIVED        = 4 
    MAIL_READY      = 5
    READY           = 6
    READY_IMPORTED  = 7
    def __str__(self):
        _AS_STRS = {AanvraagStatus.DELETED: 'verwijderd', AanvraagStatus.NEW: 'nog niet bekend', AanvraagStatus.IMPORTED_PDF: 'gelezen (PDF)',  
                AanvraagStatus.NEEDS_GRADING: 'te beoordelen', AanvraagStatus.GRADED: 'beoordeeld', 
                AanvraagStatus.ARCHIVED: 'gearchiveerd', AanvraagStatus.MAIL_READY: 'mail klaar voor verzending', AanvraagStatus.READY: 'geheel verwerkt', 
                AanvraagStatus.READY_IMPORTED: 'verwerkt (ingelezen via Excel)'}
        return _AS_STRS.get(self,_UNKNOWN)
    @staticmethod
    def valid_states()->set[AanvraagStatus]:
        return {status for status in AanvraagStatus} - {AanvraagStatus.DELETED}
        
class MijlpaalStatus(IntEnum):
    NEW             = 0
    NEEDS_GRADING   = 1
    GRADED          = 2
    READY           = 3
    def __str__(self):
        _MS_STRS = {MijlpaalStatus.NEW: 'nieuw', MijlpaalStatus.NEEDS_GRADING: 'te beoordelen', MijlpaalStatus.GRADED: 'beoordeeld', 
                MijlpaalStatus.READY: 'geheel verwerkt'}
        return _MS_STRS.get(self, _UNKNOWN)

class MijlpaalBeoordeling(IntEnum):
    TE_BEOORDELEN = 0
    ONVOLDOENDE   = 1
    VOLDOENDE     = 2
    def __str__(self):
        _MB_STRS = {MijlpaalBeoordeling.TE_BEOORDELEN: '', MijlpaalBeoordeling.ONVOLDOENDE: 'onvoldoende', MijlpaalBeoordeling.VOLDOENDE: 'voldoende'}
        return _MB_STRS.get(self,_UNKNOWN)
