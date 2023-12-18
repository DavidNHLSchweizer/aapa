from data.classes.student_directories import StudentDirectory
from data.storage.aapa_storage import AAPAStorage


class StudentDirectoryReporter:
    def report(self, storage: AAPAStorage):
        print('STUDENT-DIRECTORIES:')
        for student_directory in storage.find_all('student_directories'):
            print(student_directory)
        print('.... READY')



