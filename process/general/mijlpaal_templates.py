from enum import Enum, auto
from pathlib import Path
from mailmerge import MailMerge
from data.classes.files import File
from data.general.const import MijlpaalType, FileType
from general.fileutil import file_exists
from main.config import ListValueConvertor, config, get_templates
from main.log import log_error, log_exception
from process.forms.creating.aanvraag_form_creator import MailMergeException
from process.input.importing.filename_parser import FileTypeDetector


def init_config():
    config.register('templates', 'forms', ListValueConvertor)
    config.init('templates', 'forms', ['v2.2b', 'v2.3b', 'v3.0.0b', 'v4.0.0b', 'v5.0.0b'])
    config.init('templates', 'forms_directory', 'forms')
init_config()

class TemplateFormCreator:
    def __init__(self, template_doc: str):
        if not file_exists(template_doc):
            log_exception(f'kan template {template_doc} niet vinden.', MailMergeException)
        self.template_doc = template_doc
        self.fields = MailMerge(self.template_doc).get_merge_fields()    
    def merge_document(self, output_filename: str, preview=False, **kwds)->str:
        try:
            document = MailMerge(self.template_doc)
            if not preview:
                document.merge(**kwds)
                document.write(output_filename)
            return output_filename
        except Exception as E:
            log_error(f'Error merging document (template:{self.template_doc}) to\n\t{File.display_file(output_filename)}\n\t{E}')
            return None
    def __str__(self)->str:
        return f'<template> {self.template_doc}'

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
        forms_versions = config.get('templates', 'forms')
        self.templates = {}
        self.mijlpalen = {}
        for version in forms_versions:
            self.templates[version], self.mijlpalen[version] = self._read_version_directory(template_dir, version)
    @property
    def versions(self)->list[str]:
        return self.templates.keys()
    def _read_version_directory(self, template_dir: Path, version: str)->tuple[dict,set]:
        detector = FileTypeDetector()
        result = {}
        mijlpalen = set()
        for file in template_dir.joinpath(version).glob('*.docx'):
            _,mijlpaal_type=detector.detect(file)
            result[mijlpaal_type] = file
            mijlpalen.add(mijlpaal_type)
        return result,mijlpalen        
    def _get_verslag_form_name(self, mijlpaal_type: MijlpaalType, examinator: int)->str:
        prefixes = {MijlpaalType.PVA: '3. ', MijlpaalType.ONDERZOEKS_VERSLAG: '4. ', MijlpaalType.TECHNISCH_VERSLAG: '5. ', MijlpaalType.EIND_VERSLAG: '5. ', 
                MijlpaalType.PRODUCT_BEOORDELING: '6. ', MijlpaalType.PRESENTATIE: '7. ', MijlpaalType.EINDBEOORDELING: '8. '}
        postfixes = {FileType.GRADE_FORM_DOCX: ' gezamenlijk', FileType.GRADE_FORM_EX1_DOCX: ' ex1', FileType.GRADE_FORM_EX2_DOCX: ' ex2', FileType.GRADE_FORM_EX3_DOCX: ' ex3'}
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
    def get_verslag_names(self, version: str, mijlpaal_type: MijlpaalType, examinator: int)->tuple[str,TemplateFormCreator]:
        if not (version_templates := self.templates.get(version,None)):
            raise Exception(f'Templates voor versie {version} zijn niet gedefinieerd')
        if (template := version_templates.get(mijlpaal_type, None)):
            return (self._get_verslag_form_name(mijlpaal_type, examinator),TemplateFormCreator(template))
        else:
            return (None,None)