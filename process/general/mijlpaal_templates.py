from enum import Enum, auto
from pathlib import Path
from data.general.const import MijlpaalType, FileType
from main.config import ListValueConvertor, config, get_templates
from process.input.importing.filename_parser import FileTypeDetector


def init_config():
    config.register('templates', 'forms', ListValueConvertor)
    config.init('templates', 'forms', ['v2.2b', 'v2.3b', 'v3.0.0b', 'v4.0.0b', 'v5.0.0b'])
    config.init('templates', 'forms_directory', 'forms')
init_config()

ALL_EXAMINATORS = 0
class MijlpaalTemplates:
    class MijlpaalTemplate(Enum):
        PVA = auto()
        ONDERZOEKS_VERSLAG  = auto()
        TECHNISCH_VERSLAG   = auto()
        EIND_VERSLAG        = auto()
        PRODUCT_BEOORDELING = auto()
        PRESENTATIE         = auto()
        EINDBEOORDELING     = auto()
    def __init__(self):
        template_dir = get_templates(config.get('templates', 'forms_directory'))
        versions = config.get('templates', 'forms')
        self.templates = {}
        for version in versions:
            self.templates[version] = self._read_version_directory(template_dir, version)
    def _read_version_directory(self, template_dir: Path, version: str)->dict:
        detector = FileTypeDetector()
        result = {}
        for file in template_dir.joinpath(version).glob('*.docx'):
            _,mijlpaal_type=detector.detect(file)
            result[mijlpaal_type] = file
        return result        
    def _get_verslag_form_name(self, mijlpaal_type: MijlpaalType, examinator: int)->str:
        prefixes = {MijlpaalType.PVA: '3. ', MijlpaalType.ONDERZOEKS_VERSLAG: '4. ', MijlpaalType.TECHNISCH_VERSLAG: '5. ', MijlpaalType.EIND_VERSLAG: '5. ', 
                MijlpaalType.PRODUCT_BEOORDELING: '6. ', MijlpaalType.PRESENTATIE: '7. ', MijlpaalType.EINDBEOORDELING: '8. '}
        postfixes = {FileType.GRADE_FORM_EX1_DOCX: ' ex1', FileType.GRADE_FORM_EX2_DOCX: ' ex2', FileType.GRADE_FORM_EX3_DOCX: ' ex3'}
        if mijlpaal_type.has_single_examinator():
            filetype = FileType.GRADE_FORM_DOCX
            postfix = ''
        else:
            if examinator == ALL_EXAMINATORS:                
                filetype = FileType.GRADE_FORM_DOCX
            elif examinator == 1:                
                filetype = FileType.GRADE_FORM_EX1_DOCX
            elif examinator == 2:
                filetype = FileType.GRADE_FORM_EX2_DOCX
            elif examinator == 3:
                filetype = FileType.GRADE_FORM_EX3_DOCX
            else:
                filetype = FileType.GRADE_FORM_DOCX
            postfix = postfixes.get(filetype, '')
        if mijlpaal_type == MijlpaalType.PRODUCT_BEOORDELING:
            what = 'product'
        else:
            what = str(mijlpaal_type).lower()
        if mijlpaal_type == MijlpaalType.EINDBEOORDELING:
            return 'Eindbeoordeling afstuderen'
        else:
            return f'{prefixes.get(mijlpaal_type, '')}Beoordeling {what}{postfix}'
    def get_verslag_names(self, version: str, mijlpaal_type: MijlpaalType, examinator: int)->tuple[str,str]:
        if not (version_templates := self.templates.get(version,None)):
            raise Exception(f'Templates voor versie {version} zijn niet gedefinieerd')
        if (template := version_templates.get(mijlpaal_type, None)):
            return (self._get_verslag_form_name(mijlpaal_type, examinator),template)
        else:
            return (None,None)