from __future__ import annotations
from ast import Tuple

from pathlib import Path
import re
from data.classes.const import MijlpaalType
from data.classes.files import File

class FileTypeDetector:
    def __init__(self, regex: str, mijlpaal_type: MijlpaalType):
        self.pattern = re.compile(regex, re.IGNORECASE)
        self.filetype = File.Type.UNKNOWN
        self.mijlpaal_type = mijlpaal_type
        self.match: re.Match = None
    def _detect(self, filename: str)->bool:
        self.match = self.pattern.match(Path(filename).name)
        return self.match is not None
    @staticmethod
    def _is_docx(filename: str)->bool:
        return Path(filename).suffix.lower() == '.docx'
    def parse(self, filename: str)->Tuple[File.Type, MijlpaalType]:
        if self._detect(filename):
            return (File.Type.GRADE_FORM_DOCX if self._is_docx(filename) else File.Type.GRADE_FORM_PDF, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)

class AanvraagDetector(FileTypeDetector):
    def __init__(self):
        super().__init__(rf'Beoordeling aanvraag (?P<who>.*)\-\d+\.(docx|pdf)', mijlpaal_type=MijlpaalType.AANVRAAG)
    def parse(self, filename: str)->File.Type:
        if self._detect(filename):
            if self._is_docx(filename):
                filetype = File.Type.GRADE_FORM_DOCX
            else:
                filetype = File.Type.GRADE_FORM_PDF
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)
    

class PlanVanAanpakDetector(FileTypeDetector):
    def __init__(self):
        super().__init__(rf'3. Beoordeling plan van aanpak(?P<who>.*)?.(docx|pdf)', mijlpaal_type=MijlpaalType.PVA)
    def parse(self, filename: str)->File.Type:
        if self._detect(filename):
            if self._is_docx(filename):
                filetype = File.Type.GRADE_FORM_DOCX
            else:
                filetype = File.Type.GRADE_FORM_PDF
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)
 

class _BeoordelingDetector(FileTypeDetector):
    def __init__(self, n: int, what: str, mijlpaal_type: MijlpaalType, beoord: str='Beoordeling'):
        def _regex(n: int, what: str, beoord: str)->str:
            first_part = rf'{n}\. ' if n else ''
            return rf'{first_part}{beoord} {what} (?P<who>ex1|ex2|ex3|gezamenlijk)?(.*)?\.(docx|pdf)'
        super().__init__(_regex(n, what, beoord), mijlpaal_type=mijlpaal_type)
    def parse(self, filename: str)->File.Type:
        TRANSLATOR = {
                        True: {'ex1': File.Type.GRADE_FORM_EX1_DOCX,
                                'ex2': File.Type.GRADE_FORM_EX2_DOCX,
                                'ex3': File.Type.GRADE_FORM_EX2_DOCX,
                              },
                        False: {'ex1': File.Type.GRADE_FORM_PDF,
                                'ex2': File.Type.GRADE_FORM_PDF,
                                'ex3': File.Type.GRADE_FORM_PDF,
                              }
                      }
        if self._detect(filename):
            who = self.match.group('who')
            if not (filetype := TRANSLATOR[self._is_docx(filename)].get(who, None)):
                if who and who[:5] == 'gezam':
                    filetype = File.Type.GRADE_FORM_DOCX
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)

class OnderzoeksVerslagDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(4, 'onderzoeksverslag', mijlpaal_type=MijlpaalType.ONDERZOEKS_VERSLAG)

class TechnischVerslagDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(5, 'technisch verslag', mijlpaal_type=MijlpaalType.TECHNISCH_VERSLAG)

class EindVerslagDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(5, 'eindverslag', mijlpaal_type=MijlpaalType.EIND_VERSLAG)

class ProductBeoordelingDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(6, 'product', mijlpaal_type=MijlpaalType.PRODUCT_BEOORDELING)

class PresentatieBeoordelingDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(7, 'presentatie', mijlpaal_type=MijlpaalType.PRESENTATIE)

class EindBeoordelingDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(8, 'afstuderen', mijlpaal_type=MijlpaalType.EINDBEOORDELING, beoord='Eindbeoordeling')

class FileTypeDetector:
    def __init__(self):
        self.detectors: list[FileTypeDetector] = [AanvraagDetector(), 
                                                  PlanVanAanpakDetector(), 
                                                  OnderzoeksVerslagDetector(), 
                                                  TechnischVerslagDetector(), 
                                                  ProductBeoordelingDetector(), 
                                                  EindVerslagDetector(),
                                                  PresentatieBeoordelingDetector(),
                                                  EindBeoordelingDetector()
                                                  ]
    def detect(self, filename: str)->(File.Type, MijlpaalType):
        for detector in self.detectors:
            (filetype,mijlpaal_type) = detector.parse(filename) 
            if filetype != File.Type.UNKNOWN:
                return (filetype, mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)
    
        
