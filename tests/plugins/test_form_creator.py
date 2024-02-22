
from argparse import ArgumentParser
import datetime
from pathlib import Path

from mailmerge import MailMerge

from data.classes.files import File
from data.classes.student_directories import StudentDirectory
from data.general.const import MijlpaalType
from data.classes.studenten import Student
from general.fileutil import file_exists
from general.timeutil import TSC
from main.log import log_error, log_exception, log_print
from general.sql_coll import import_json
from plugins.plugin import PluginBase
from process.general.mijlpaal_templates import ALL_EXAMINATORS, MijlpaalTemplates, TemplateFormCreator
from process.general.student_dir_builder import StudentDirectoryBuilder
from process.input.create_forms.create_form import MailMergeException
from process.main.aapa_processor import AAPARunnerContext
from random_student import RandomStudents
from storage.queries.student_directories import StudentDirectoryQueries
from storage.queries.studenten import StudentQueries


class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.student_dir_queries: StudentDirectoryQueries = context.storage.queries('student_directories')
        self.builder = StudentDirectoryBuilder(self.storage)
        self.templates = MijlpaalTemplates()
        return True
    def __get_kans_str(self, kans: int)->str:
        match kans:
            case 1: kans_str = 'eerste'
            case 2: kans_str = 'tweede'
            case 3: kans_str = 'derde'
            case _: kans_str = 'tig-ste'
        return f'{kans_str} kans'

    def _generate_fields(self, student: Student, kans: int, titel: str, bedrijf: str, datum: datetime.datetime, select_fields: set)->dict:       
        def test_include(result: dict, key: str, value: str):
            if key in select_fields: result[key] = value
        result = {}
        test_include(result, 'student', student.full_name)
        test_include(result, 'studentnummer', student.stud_nr)
        test_include(result, 'kans', self.__get_kans_str(kans))
        test_include(result, 'titel', titel)
        test_include(result, 'bedrijf', bedrijf)
        test_include(result, 'datum', TSC.get_date_str(datum))
        return result
    def _generate_form(self, creator: TemplateFormCreator, student: Student, bedrijf: str, kans: int, titel: str, datum: datetime.datetime, filename: str, preview=False)->bool:
        fields_data = self._generate_fields(student=student, bedrijf=bedrijf, kans=kans, titel=titel, datum=datum, select_fields=creator.fields)
        if preview:
            print(f'Plan: Merging to {filename}. values: {fields_data}.')
            return True
        else:
            print(f'Fields: {fields_data}')
            return creator.merge_document(filename, preview, **fields_data) is not None
    def _generate_forms_info(self, forms_version, directory: Path, mijlpaal_type: MijlpaalType)->dict:
        def form_for_examinator(directory: Path, forms_version: str, mijlpaal_type: MijlpaalType, examinator: int)->dict:
            (form_name, creator) = self.templates.get_verslag_names(forms_version, mijlpaal_type, examinator)
            return {'filename': f'{directory.joinpath(form_name)}.docx', 'creator': creator}
        results = {}
        results[ALL_EXAMINATORS] = form_for_examinator(directory, forms_version, mijlpaal_type, ALL_EXAMINATORS)
        if not mijlpaal_type.has_single_examinator():
            for examinator in range(1,3):
                results[examinator] = form_for_examinator(directory, forms_version, mijlpaal_type, examinator)
        return results        
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        rs = RandomStudents(context.storage, Student.Status.active_states())
        student = rs.random_student()
        print(f'student: {student}')
        stud_dir = self.student_dir_queries.find_student_dir(student)
        version = stud_dir.base_dir.forms_version
        datum = datetime.datetime.now()
        mijlpaal_type=MijlpaalType.ONDERZOEKS_VERSLAG
        for version in self.templates.versions:
            print(f'Versie: {version}')
            if not mijlpaal_type in self.templates.mijlpalen[version]:
                print(f'geen {mijlpaal_type} in versie {version}.')
                continue
            forms = self._generate_forms_info(version, Path(self.builder.get_mijlpaal_directory_name(stud_dir, datum, mijlpaal_type)), mijlpaal_type)
            for _,value in forms.items():
                for kans in range(1,3):
                    fn = Path(r'd:\tempo').joinpath(Path(value['filename']).stem+f'_kans_{kans}.{version}.docx')
                    self._generate_form(value['creator'], student=student, bedrijf='Waldolola', kans=kans, titel='Oekelen in de marge', datum=datetime.date.today(), filename=fn, preview=context.preview)


        # for mijlpaal_type in MijlpaalType.verslag_types():
        #     if mijlpaal_type in self.templates.mijlpalen[version]:
        #         forms = self._generate_forms_info(version, Path(self.builder.get_mijlpaal_directory_name(stud_dir, datum, mijlpaal_type)), mijlpaal_type)
        #         for key,value in forms.items():
        #             for kans in range(1,3):
        #                 fn = Path(r'd:\tempo').joinpath(Path(value['filename']).stem+f'_kans_{kans}.docx')
        #                 self._generate_form(value['creator'], student, 'Waldolola', kans, 'Oekelen in de marge', datetime.date.today(), fn, preview=context.preview)
        return True
    