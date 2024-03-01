
from copy import deepcopy
import tkinter.simpledialog as tksimp
from data.classes.aanvragen import Aanvraag
from data.classes.studenten import Student
from storage.aapa_storage import AAPAStorage
from storage.queries.aanvragen import AanvragenQueries
from storage.queries.studenten import StudentenQueries
from main.log import log_error, log_warning
from general.valid_email import is_valid_email, try_extract_email
from process.general.pdf_aanvraag_reader import is_valid_title

class AanvraagValidator:
    def __init__(self, storage: AAPAStorage, source_file: str, aanvraag: Aanvraag):
        self.storage = storage
        self.source_file = source_file
        self.validated_aanvraag = deepcopy(aanvraag)
    def validate(self)->bool:
        if not self.__check_email():
            return False
        if not self.__check_titel():
            return False
        if not self.__check_student():
            return False
        self.__insert_versie_en_kans()
        if self.validated_aanvraag.student.status == Student.Status.UNKNOWN:
            self.validated_aanvraag.student.status = Student.Status.AANVRAAG
        return True
    def __check_student(self)->bool:
        queries: StudentenQueries = self.storage.queries('studenten')
        if stored_student := queries.find_student_by_name_or_email_or_studnr(self.validated_aanvraag.student):
            self.validated_aanvraag.student = stored_student
        return True
    def __check_email(self)->bool:
        if not is_valid_email(self.validated_aanvraag.student.email):
            new_email = try_extract_email(self.validated_aanvraag.student.email, True)
            if new_email:
                new_email = new_email.lower()
                log_warning(f'Aanvraag email is ongeldig:\n\t({self.validated_aanvraag.student.email}),\n\taangepast als {new_email}.')
                self.validated_aanvraag.student.email = new_email
            else:
                log_error(f'Aanvraag email is ongeldig: {self.validated_aanvraag.student.email}')
                return False
        return True
    def __check_titel(self)->bool:
        if not is_valid_title(self.validated_aanvraag.titel):
            self.validated_aanvraag.titel=self.__ask_titel(self.validated_aanvraag)
        return True
    def __ask_titel(self, aanvraag: Aanvraag)->str:
        return tksimp.askstring(f'Titel', f'Titel voor {str(aanvraag)}', initialvalue=aanvraag.titel)
    def __insert_versie_en_kans(self):
        queries: AanvragenQueries = self.storage.queries('aanvragen')
        bedrijf = self.validated_aanvraag.bedrijf
        student = self.validated_aanvraag.student
        kans = queries.find_kans(student)
        self.validated_aanvraag.kans = (kans + 1) if kans else 1
        versie = queries.find_versie(student, bedrijf)
        self.validated_aanvraag.versie = (versie + 1) if versie else 1 
