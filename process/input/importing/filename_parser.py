from __future__ import annotations
from ast import Tuple

from pathlib import Path
import re
from data.general.const import MijlpaalType
from data.classes.files import File

class FilenameDetector:
    def __init__(self, regex_list: list[str], mijlpaal_type: MijlpaalType):
        self.patterns = [re.compile(regex, re.IGNORECASE) for regex in regex_list]
        self.filetype = [File.Type.UNKNOWN] * len(self.patterns)
        self.mijlpaal_type = mijlpaal_type
        self.match: re.Match = None
    def _detect(self, filename: str)->int:
        for n,pattern in enumerate(self.patterns):
            self.match = pattern.match(Path(filename).name)
            if self.match:
                return n
        return -1
    @staticmethod
    def _is_docx(filename: str)->bool:
        return Path(filename).suffix.lower() == '.docx'
    def get_grade_form_type(self, is_docx: bool)->File.Type:
        TRANSLATOR = {
                        True: { 'ex1': File.Type.GRADE_FORM_EX1_DOCX,
                                'ex2': File.Type.GRADE_FORM_EX2_DOCX,
                                'ex3': File.Type.GRADE_FORM_EX3_DOCX,
                              },
                        False: {'ex1': File.Type.GRADE_FORM_PDF,
                                'ex2': File.Type.GRADE_FORM_PDF,
                                'ex3': File.Type.GRADE_FORM_PDF,
                              }
                      }
        DEFAULT = { True: File.Type.GRADE_FORM_DOCX, False: File.Type.GRADE_FORM_PDF}
        if self.match.group('who'):
            who_str = self.match.group('who').strip()[:3]
        else:
            who_str = '' 
        # print(self.pattern, who_str)
        return TRANSLATOR[is_docx].get(who_str, DEFAULT[is_docx])
    def detect(self, filename: str)->Tuple[File.Type, MijlpaalType]:
        if self._detect(filename) >= 0:
            return (File.Type.GRADE_FORM_DOCX if self._is_docx(filename) else File.Type.GRADE_FORM_PDF, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)

class AanvraagDetector(FilenameDetector):
    def __init__(self):
        super().__init__([
                        rf'1. Aanvraag toelating afstuderen(?P<who>.*)?(\-\d+\))?.(docx|pdf)',
                        rf'2. Beoordeling afstudeeropdracht(?P<who>.*)?(\-\d+\))?.(docx|pdf)',
                        rf'Beoordeling aanvraag(?P<who>.*)(\-\d+\))?.(docx|pdf)',
                          ], 
                         mijlpaal_type=MijlpaalType.AANVRAAG)
    def detect(self, filename: str)->File.Type:
        if (detected := self._detect(filename)) >= 0:
            if detected == 0:
                if self._is_docx(filename):
                    filetype = File.Type.INVALID_DOCX
                else:
                    filetype = File.Type.INVALID_PDF
            elif detected == 1:
                if self._is_docx(filename):
                    filetype = File.Type.AANVRAAG_OTHER
                else:
                    filetype = File.Type.AANVRAAG_PDF
            else:
                if self._is_docx(filename):
                    filetype = File.Type.GRADE_FORM_DOCX
                else:
                    filetype = File.Type.GRADE_FORM_PDF
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)

class PlanVanAanpakDetector(FilenameDetector):
    def __init__(self):
        super().__init__([rf'3. Beoordeling plan van aanpak(?P<who>.*)?(.*)?\.(docx|pdf)'], 
                         mijlpaal_type=MijlpaalType.PVA)
    def detect(self, filename: str)->File.Type:
        if self._detect(filename)>=0:
            filetype = self.get_grade_form_type(self._is_docx(filename))
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)

class _BeoordelingDetector(FilenameDetector):
    def __init__(self, n: int, what: str, mijlpaal_type: MijlpaalType, beoord: str='Beoordeling'):
        def _regex(n: int, what: str, beoord: str)->str:
            first_part = rf'{n}\. ' if n else ''
            return rf'{first_part}{beoord} {what}(\s|\s-\s|\.)?(?P<who>ex1|ex2|ex3|gezamenlijk)?(.*)?\.(docx|pdf)'
        super().__init__([_regex(n, what, beoord)], mijlpaal_type=mijlpaal_type)
    def detect(self, filename: str)->File.Type:
        if self._detect(filename)>=0:
            filetype = self.get_grade_form_type(self._is_docx(filename))
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

class ProductBeoordelingDetector(FilenameDetector):
    def __init__(self):
        super().__init__([rf'6.[\s|_|\+]Beoordeling[\s|_|\+]product(?P<who>.*)?(.*)?\.(docx|pdf)'], 
                         mijlpaal_type=MijlpaalType.PRODUCT_BEOORDELING)
    def detect(self, filename: str)->File.Type:
        if self._detect(filename)>=0:
            filetype = self.get_grade_form_type(self._is_docx(filename))
            return (filetype, self.mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)
    # def __init__(self):
    #     super().__init__(6, 'product', mijlpaal_type=MijlpaalType.PRODUCT_BEOORDELING)

class PresentatieBeoordelingDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(7, 'presentatie', mijlpaal_type=MijlpaalType.PRESENTATIE)

class EindBeoordelingDetector(_BeoordelingDetector):
    def __init__(self):
        super().__init__(8, 'afstuderen', mijlpaal_type=MijlpaalType.EINDBEOORDELING, beoord='Eindbeoordeling')

class FileTypeDetector:
    def __init__(self):
        self.detectors: list[FilenameDetector] = [AanvraagDetector(), 
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
            (filetype,mijlpaal_type) = detector.detect(filename) 
            if filetype != File.Type.UNKNOWN:
                return (filetype, mijlpaal_type)
        return (File.Type.UNKNOWN,MijlpaalType.UNKNOWN)
    
        
