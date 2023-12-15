from __future__ import annotations
from ast import Tuple

from pathlib import Path
import re
from data.classes.files import File
from data.classes.verslagen import Mijlpaal

class FileTypeDetector:
    def __init__(self, regex: str, mijlpaal_type: Mijlpaal.Type):
        self.pattern = re.compile(regex)
        self.filetype = File.Type.UNKNOWN
        self.mijlpaal_type = mijlpaal_type
        self.match: re.Match = None
    def _detect(self, filename: str)->bool:
        self.match = self.pattern.match(Path(filename).name)
        return self.match is not None
    @staticmethod
    def _is_docx(filename: str)->bool:
        return Path(filename).suffix.lower() == '.docx'
    def parse(self, filename: str)->Tuple[File.Type, Mijlpaal.Type]:
        if self._detect(filename):
            return (File.Type.GRADE_FORM_DOCX if self._is_docx(filename) else File.Type.GRADE_FORM_PDF, self.mijlpaal_type)
        return (File.Type.UNKNOWN,Mijlpaal.Type.UNKNOWN)
    
class PlanVanAanpakDetector(FileTypeDetector):
    def __init__(self):
        super().__init__(r'3\. Beoordeling plan van aanpak(.*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.PVA)
        
class VerslagDetector(FileTypeDetector):
    def __init__(self, regex: str, mijlpaal_type: Mijlpaal.Type):
        super().__init__(regex, mijlpaal_type=mijlpaal_type)
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
            if not (filetype := TRANSLATOR[self._is_docx(filename)].get(self.match.group('who'))):
                if self.match.group('who')[:5] == 'gezam':
                    filetype = File.Type.GRADE_FORM_DOCX
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,Mijlpaal.Type.UNKNOWN)

class OnderzoeksVerslagDetector(VerslagDetector):
    def __init__(self):
        super().__init__(r'4\. Beoordeling onderzoeksverslag (?P<who>ex1|ex2|ex3|gezamenlijk)(.*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.ONDERZOEKS_VERSLAG)

class TechnischVerslagDetector(VerslagDetector):
    def __init__(self):
        super().__init__(r'5\. Beoordeling technisch verslag (?P<who>ex1|ex2|ex3|gezamenlijk)(.*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.TECHNISCH_VERSLAG)

class EindVerslagDetector(VerslagDetector):
    def __init__(self):
        super().__init__(r'5\. Beoordeling eindverslag (?P<who>ex1|ex2|ex3|gezamenlijk)(.*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.EIND_VERSLAG)

class ProductBeoordelingDetector(FileTypeDetector):
    def __init__(self):
        super().__init__(r'6\. Beoordeling product(?P<who>[\s\-].*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.PRODUCT_BEOORDELING)

class PresentatieBeoordelingDetector(FileTypeDetector):
    def __init__(self):
        super().__init__(r'7\. Beoordeling presentatie(?P<who>[\s\-].*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.PRESENTATIE)

class EindBeoordelingDetector(FileTypeDetector):
    def __init__(self):
        super().__init__(r'8\. Eindbeoordeling afstuderen(.*)?\.(docx|pdf)', mijlpaal_type=Mijlpaal.Type.EINDBEOORDELING)

class FileTypeDetector:
    def __init__(self):
        self.detectors: list[FileTypeDetector] = [PlanVanAanpakDetector(), 
                                                  OnderzoeksVerslagDetector(), 
                                                  TechnischVerslagDetector(), 
                                                  ProductBeoordelingDetector(), 
                                                  EindVerslagDetector(),
                                                  PresentatieBeoordelingDetector(),
                                                  EindBeoordelingDetector()
                                                  ]
    def detect(self, filename: str)->(File.Type, Mijlpaal.Type):
        for detector in self.detectors:
            (filetype,mijlpaal_type) = detector.parse(filename) 
            if filetype != File.Type.UNKNOWN:
                return (filetype, mijlpaal_type)
        return (File.Type.UNKNOWN,Mijlpaal.Type.UNKNOWN)
    
        
