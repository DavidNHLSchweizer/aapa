
from data.classes.files import File
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.general.aapa_class import AAPAclass
from general.classutil import classname

class ClassCodeException(Exception): pass
class ClassCodes:
    _codes = { 
        'AV': Aanvraag, 
        'BD': Bedrijf, 
        'FL': File,
        'MP': MijlpaalDirectory,
        'ST': Student,
        'SD': StudentDirectory,
        'VS': Verslag,               
        }
    @staticmethod
    def classtype_to_code(aapa_class: AAPAclass)->str:
        for code,class_type in ClassCodes._codes.items():
            if class_type == aapa_class:
                return code
        raise ClassCodeException(f'Unsupported class {classname(aapa_class)}')
    @staticmethod
    def code_to_classtype(code: str)->AAPAclass:
        if class_type := ClassCodes._codes.get(code, None):
            return class_type
        raise ClassCodeException(f'Unsupported detail class code {code}')

