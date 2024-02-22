
from argparse import ArgumentParser
import datetime
from pathlib import Path

from data.classes.files import File
from data.classes.student_directories import StudentDirectory
from data.general.const import MijlpaalType
from data.classes.studenten import Student
from main.log import log_error, log_print
from general.sql_coll import import_json
from plugins.plugin import PluginBase
from process.general.mijlpaal_templates import ALL_EXAMINATORS, MijlpaalTemplates
from process.general.student_dir_builder import StudentDirectoryBuilder
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
    def _generate_forms(self, forms_version, directory: Path, mijlpaal_type: MijlpaalType)->dict:
        def form_for_examinator(directory: Path, forms_version: str, mijlpaal_type: MijlpaalType, examinator: int)->dict:
            (form_name, template) = self.templates.get_verslag_names(forms_version, mijlpaal_type, examinator)
            return {'filename': directory.joinpath(form_name), 'template': template}
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
        for mijlpaal_type in MijlpaalType.verslag_types():
            if mijlpaal_type in self.templates.mijlpalen[version]:
                forms = self._generate_forms(version, Path(self.builder.get_mijlpaal_directory_name(stud_dir, datum, mijlpaal_type)), mijlpaal_type)
                for key,value in forms.items():
                    print(f'\t{key}: template {value['template']}\n\tfilename: {File.display_file(value['filename'])}')
        return True
    