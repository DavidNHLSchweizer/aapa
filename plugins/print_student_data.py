""" Print student data in database.

    Plugin to print a "pretty print tree" view of the student data as in the database.

    Syntax:
        python run_plugin.py print_student_data --student="student name" [--width=value]

    "student name" can be either full name (first_name last_name) with or without 'tussenvoegsels'
    or first name(s) or last_name.
    If more than one students has that name, all of them are printed.      

    If the tree is too small or too large for your terminal screen, you can adjust the width of each part a bit.

"""
from argparse import ArgumentParser
from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.general.aapa_class import AAPAclass
from data.general.class_codes import ClassCodes
from data.classes.files import File
from general.name_utils import Names
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from PrettyPrint import PrettyPrintTree

DEFAULT_WIDTH = 40
class AAPATreePrinter:
    def __init__(self, trim_width = DEFAULT_WIDTH):
        self.print_tree = PrettyPrintTree(self.get_children, self.get_value, trim=trim_width, orientation=PrettyPrintTree.Horizontal)
        self.top_level_type = None
    def get_children(self, node: AAPAclass)->list[AAPAclass]:
        if isinstance(node, StudentDirectory):
            return node.directories
        elif isinstance(node, MijlpaalDirectory):
            return node.items
        elif isinstance(node, Aanvraag|Verslag):
            return node.files_list
        elif isinstance(node,File):
            return None
    def _get_filename(self, filename: str, is_top_level=False):
        if is_top_level:
            return File.display_file(filename)
        else:
            return Path(filename).name
    def get_value(self, node: AAPAclass)->str:
        id_part= f'{ClassCodes.classtype_to_code(type(node))}{node.id}'
        if isinstance(node, StudentDirectory):
            if node.status == StudentDirectory.Status.ARCHIVED:
                id_part = id_part + '(ARCH)'
            info_part = self._get_filename(node.directory, type(node)==self.top_level_type)

        elif isinstance(node, MijlpaalDirectory):
            info_part = self._get_filename(node.directory, type(node)==self.top_level_type)
        elif isinstance(node, Aanvraag|Verslag):
            info_part = node.summary()
        elif isinstance(node, File):
            info_part= self._get_filename(node.filename, type(node)==self.top_level_type)
        return f'{id_part}:{info_part}'
    def print(self, node: object):
        self.top_level_type = type(node)
        self.print_tree(node)
    
class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        self.students: list[Student] = self.storage.find_all('studenten')
        return True
    def detect_studenten(self, student_name: str)->list[Student]:
        parsed = Names.parsed(student_name)
        result = []
        for student in self.students:
            parsed_student = Names.parsed(student.full_name)
            if parsed_student.first_name.lower() == parsed.first_name.lower() and parsed_student.last_name.lower() == parsed.last_name.lower():
                result.append(student)
        if not result:                
            for student in self.students:
                parsed_student = Names.parsed(student.full_name)
                if parsed_student.first_name.lower() == parsed.first_name.lower() or parsed_student.last_name.lower() == parsed.last_name.lower() or \
                    parsed_student.first_name.lower() == student_name.lower():
                    result.append(student)
        return result
    def get_parser(self) -> ArgumentParser:               
        parser = super().get_parser()
        parser.add_argument('--student', type=str, help='(gedeeltelijke) naam van de student. Verwacht wordt "Voornaam Achternaam".\nAlle studenten die deze (gedeeltelijke) naam hebben worden afgedrukt.')
        parser.add_argument('-width', '--width', dest='width', type=int, help=f'Gebruik dit om de "breedte" van de boom in te stellen. Default is {DEFAULT_WIDTH}.')
        return parser   
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:   
        width = kwdargs.get('width', DEFAULT_WIDTH)
        if not width:
            width = DEFAULT_WIDTH
        printer = AAPATreePrinter(width)

        if not (studenten := self.detect_studenten(kwdargs.get('student', ''))):
            print(f'Student wordt niet herkend: {kwdargs.get('student', '')}')
        else:
            for student in studenten:
                print(f'STUDENT: {student}')
                for directory in self.storage.find_all('student_directories', where_attributes='student', where_values=student):
                    printer.print(directory)
                    print()
        return True
    