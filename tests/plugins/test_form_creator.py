
from argparse import ArgumentParser
import datetime
from pathlib import Path
import random

from data.classes.files import File
from data.classes.verslagen import Verslag
from data.general.const import MijlpaalType
from data.classes.studenten import Student
from plugins.plugin import PluginBase
from process.forms.creating.verslag_version_forms_creator import VerslagVersionFormsCreator

from process.general.student_dir_builder import StudentDirectoryBuilder
from process.main.aapa_processor import AAPARunnerContext
from storage.queries.student_directories import StudentDirectoryQueries
from tests.random_data import RandomData

    
class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.student_dir_queries: StudentDirectoryQueries = context.storage.queries('student_directories')
        self.builder = StudentDirectoryBuilder(self.storage)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        rs = RandomData(context.storage, Student.Status.active_states())
        student = rs.random_student()
        bedrijf = rs.random_bedrijf()
        print(f'student: {student}')
        stud_dir = self.student_dir_queries.find_student_dir(student) 
        version = stud_dir.base_dir.forms_version
        SVC = VerslagVersionFormsCreator(self.storage, version)
        for mijlpaal_type in MijlpaalType.verslag_types():
            if not mijlpaal_type in SVC.mijlpalen:
                continue
            print(f'MIJLPAAL: {mijlpaal_type}')
            verslag = Verslag(mijlpaal_type, student, datum = rs.random_date(), bedrijf=bedrijf, kans=random.randrange(1,3),titel=rs.random_quote())
            directory = Path(self.builder.get_mijlpaal_directory_name(stud_dir, verslag.datum, mijlpaal_type))
            print(f'"echte" directory\n{File.display_file(directory)}')
            print(f'------------------------')
            created = SVC.create_forms(verslag, r'd:\tempo')
            for filename,filetype in created:
                print(f'File: {File.display_file(filename)}  filetype: {filetype}')
        return True
    