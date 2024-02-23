""" Maakt formulieren voor verslagen """
import datetime
from pathlib import Path
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.general.const import FileType, MijlpaalType
from general.timeutil import TSC
from process.general.mijlpaal_templates import ALL_EXAMINATORS, MijlpaalTemplates, TemplateFormCreator
from storage.aapa_storage import AAPAStorage

class FormCreatorException(Exception): pass
class VerslagVersionFormsCreator:
    """ class: VerslagVersionFormCreator

        Maakt beoordelingesformulieren voor individuele verslagen in de versie die bij dat verslag hoort.
    
    """
    def __init__(self, storage: AAPAStorage, forms_version: str):
        """ 
            parameters
            ----------
            storage: de storage-laag
            forms_version: de versie van forms (string, zoals te vinden in de templates/forms)

        """
        self.storage = storage
        self.templates = MijlpaalTemplates()
        self.forms_version = forms_version
        self.forms_info = self._init_forms_info()
    @property
    def mijlpalen(self)->set[MijlpaalType]:
        return set(self.forms_info.keys())
    def create_forms(self, verslag: Verslag, directory: str, preview=False)->list[tuple[str,MijlpaalType]]:                
        """ Maakt beoordelingsformulieren aan.

            parameters
            ----------
            verslag: Het verslag waarvoor formulieren worden aangemaakt
            directory: De directory waarin de formulieren worden aangemaakt. 
            preview: indien True worden alleen de filenamen teruggegeven maar niet aangemaakt
                indien False worden de files inderdaad aangemaakt met de juiste gegevens uit het verslag
                alvast ingevuld.

            returns
            -------
            lijst van aangemaakte bestanden in de vorm van een lijst [(bestandsnaam, bestandstype (File.Type))].  
        
        """
        def _generate(all_info: dict, examinator: int):
            file_types = {ALL_EXAMINATORS: FileType.GRADE_FORM_DOCX, 1: FileType.GRADE_FORM_EX1_DOCX, 2:FileType.GRADE_FORM_EX2_DOCX, 3: FileType.GRADE_FORM_EX3_DOCX,}
            info = all_info[examinator]
            filename = Path(directory).joinpath(info['filename'])
            self._generate_form(info['creator'], verslag.student, verslag.bedrijf, 
                                verslag.kans,verslag.titel, verslag.datum, examinator, 
                                filename=filename, preview=preview)
            return (str(filename),file_types.get(examinator,FileType.GRADE_FORM_DOCX))
        if not (all_info := self.forms_info.get(verslag.mijlpaal_type)):
            raise FormCreatorException(f'Verslag {verslag.summary()} hoort niet bij deze formulieren-versie {self.forms_version}')
        result = [_generate(all_info, ALL_EXAMINATORS)]
        if verslag.mijlpaal_type.has_single_examinator():
            return result
        for examinator in range(1,3):
            result.append(_generate(all_info, examinator))
        return result
    def __get_kans_str(self, kans: int)->str:
        match kans:
            case 1: kans_str = 'eerste'
            case 2: kans_str = 'tweede'
            case 3: kans_str = 'derde'
            case _: kans_str = 'tig-ste'
        return f'{kans_str} kans'
    def _generate_fields(self, student: Student, kans: int, titel: str, bedrijf: Bedrijf, datum: datetime.datetime, examinator: int, select_fields: set)->dict:       
        def test_include(result: dict, key: str, value: str):
            if key in select_fields: result[key] = value
        examinator_str={0: 'Gezamenlijk', 1: 'Examinator 1', 2: 'Examinator 2'}
        result = {key: '' for key in select_fields}
        test_include(result, 'student', student.full_name)
        test_include(result, 'studentnummer', student.stud_nr)
        test_include(result, 'kans', self.__get_kans_str(kans))
        test_include(result, 'titel', titel)
        test_include(result, 'bedrijf', bedrijf.name)
        test_include(result, 'datum', TSC.get_date_str(datum, date_format="%d %B %Y"))
        test_include(result, 'examinator', examinator_str.get(examinator, ''))
        return result
    def _generate_form(self, creator: TemplateFormCreator, student: Student, bedrijf: Bedrijf, kans: int, titel: str, datum: datetime.datetime, examinator: int, filename: str, preview=False)->bool:
        fields_data = self._generate_fields(student=student, bedrijf=bedrijf, kans=kans, titel=titel, datum=datum, examinator=examinator, select_fields=creator.fields)
        if preview:
            return True
        else:
            return creator.merge_document(filename, preview, **fields_data) is not None        
    def _mijlpaal_forms_info(self, mijlpaal_type: MijlpaalType)->dict:
        def form_for_examinator(mijlpaal_type: MijlpaalType, examinator: int)->dict:
            (form_name, creator) = self.templates.get_verslag_names(self.forms_version, mijlpaal_type, examinator)
            return {'filename': f'{form_name}.docx', 'creator': creator}
        results = {}
        results[ALL_EXAMINATORS] = form_for_examinator(mijlpaal_type, ALL_EXAMINATORS)
        if not mijlpaal_type.has_single_examinator():
            for examinator in range(1,3):
                results[examinator] = form_for_examinator(mijlpaal_type, examinator)
        return results        
    def _init_forms_info(self)->dict:
        results = {}
        for mijlpaal_type in MijlpaalType.verslag_types():
            if not mijlpaal_type in self.templates.mijlpalen[self.forms_version]:
                continue
            results[mijlpaal_type] = self._mijlpaal_forms_info(mijlpaal_type)
        return results
    