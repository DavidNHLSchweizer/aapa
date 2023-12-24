
from enum import Enum
from typing import Any, Iterable
from mailmerge import MailMerge
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student

from general.config import config
from general.fileutil import path_with_suffix
from general.strutil import replace_all
from general.timeutil import TSC
from process.general.word_processor import Word2PdfConvertor
from process.scan.importing.excel_reader import ExcelReader

def init_config():
    config.init('import', 'xls_template', r'.\templates\2. Aanvraag goedkeuring afstudeeropdracht nieuwe vorm MAILMERGE.docx')

class AanvragenFromExcelImporter:
    class ColNr(Enum):
        ID          = 0
        BEGINTIJD   = 1
        VOLTOOIEN   = 2
        EMAIL       = 3
        NAAM        = 4
        WIJZIGING   = 5
        STUDNR      = 6
        TELNR       = 7
        VT_DT       = 8
        BEDRIJF     = 9
        BEDR_ADRES  = 10
        BEDR_WWW    = 11
        BEDR_BEGL   = 12
        BEDR_BEGL_FIE  = 13
        BEDR_BEGL_EML  = 14
        BEDR_BEGL_TEL  = 15
        BRON        = 16
        START       = 17
        KERNTAKEN   = 18
        BELANG      = 19
        BEGELEIDING = 20
        TITEL       = 21
        AANLEIDING  = 22
        OMSCHRIJVING= 23
        BER_PRODUCTEN = 24
        SW_PRODUCTEN  = 25
        ONDZ_VERMOGEN = 26
        ANALYSE     = 27 
        ONTWERP     = 28
        TEST        = 29
        KWALITEIT   = 30
        TECHNIEK    = 31
    ENQUETE_COLUMNS= \
    { ColNr.ID: 'ID', 
      ColNr.BEGINTIJD: 'Begintijd', 
      ColNr.VOLTOOIEN: 'Tijd van voltooien', 
      ColNr.EMAIL: 'E-mail', 
      ColNr.NAAM: 'Naam',
      ColNr.WIJZIGING: 'Tijd van laatste wijziging', 
      ColNr.STUDNR: 'Wat is je studentnummer',
      ColNr.TELNR: 'Wat is je telefoonnummer', 
      ColNr.VT_DT: 'Hoe ga je afstuderen?',
      ColNr.BEDRIJF: 'Bij welk bedrijf ga je afstuderen?',
      ColNr.BEDR_ADRES: 'Wat is het adres van het afstudeerbedrijf?',
      ColNr.BEDR_WWW:  'Wat is de website van het bedrijf?',
      ColNr.BEDR_BEGL: 'Wat is de naam van je bedrijfsbegeleider?',
      ColNr.BEDR_BEGL_FIE: 'Wat is de functie van deze bedrijfsbegeleider?',
      ColNr.BEDR_BEGL_EML: 'Wat is het e-mail adres van deze bedrijfsbegeleider',
      ColNr.BEDR_BEGL_TEL: 'Wat is het telefoonnummer van deze bedrijfsbegeleider',
      ColNr.BRON: 'Hoe heb je deze opdracht gevonden?',
      ColNr.START: 'Wanneer wil je starten met je afstudeeropdracht?',
      ColNr.KERNTAKEN: 'Kerntaken van het bedrijf',
      ColNr.BELANG: 'Wat is het belang voor de opdrachtgever bij deze opdracht?',
      ColNr.BEGELEIDING: 'Begeleiding',
      ColNr.TITEL: '(Voorlopige, maar beschrijvende) Titel van de afstudeeropdracht',
      ColNr.AANLEIDING: 'Wat is de aanleiding voor de opdracht? \n',
      ColNr.OMSCHRIJVING: 'Korte omschrijving van de opdracht\n',
      ColNr.BER_PRODUCTEN:  'Wat zijn de op te leveren beroepsproducten uit jouw project?\n ',
      ColNr.SW_PRODUCTEN: 'Wat zijn de op te leveren softwareproduct(en) uit jouw project? \n',
      ColNr.ONDZ_VERMOGEN: 'Onderzoekend vermogen: welke ruimte is er in de opdracht om zaken te onderzoeken? \n ',
      ColNr.ANALYSE: 'Analysefase: Hoe kom je aan de (functionele/non functionele) requirements? \n',
      ColNr.ONTWERP: 'Ontwerpfase: Hoe ga je ontwerpen (werkwijze, methode) en wat ontwerp je (voorlopig)?',
      ColNr.TEST: 'Testfase: hoe kun je de kwaliteit van je softwareproduct aantonen? \n',
      ColNr.KWALITEIT: 'Kwaliteitsbewaking: welke processen ga je inzetten om grip te houden op je kwaliteit en voortgang?\n ',
      ColNr.TECHNIEK: 'Welke technieken/frameworks ga je inzetten en welke hiervan heb je nog geen ervaring mee. \n',
    }
    def __init__(self):
        self.template = config.get('import', 'xls_template')
        with MailMerge(self.template) as document:
            self.merge_fields = document.get_merge_fields()            
    def find_merge_field_vraag(self, merge_field: str)->str:
        def _standardize_vraag(vraag: str)->str:
            return replace_all(replace_all(vraag, ':/(),-', ''), ' ?\n', '_').replace('___', '__')
        for vraag in self.ENQUETE_COLUMNS.values():
            vraag2 = _standardize_vraag(vraag)
            if vraag2.find(merge_field)==0:
                return vraag
        return 'not found'
    def __get_value(self, values: dict[str, Any], colnr: ColNr)->str:
        return str(values.get(self.ENQUETE_COLUMNS.get(colnr, colnr.name)))
    def create_aanvraag(self, values: dict[str, Any])->Aanvraag:
        student = Student(full_name=self.__get_value(values, self.ColNr.NAAM),
                          stud_nr=self.__get_value(values, self.ColNr.STUDNR),
                          email=self.__get_value(values, self.ColNr.EMAIL))
        bedrijf = Bedrijf(self.__get_value(values, self.ColNr.BEDRIJF))
        return Aanvraag(student, bedrijf, 
                        datum = TSC.str_to_timestamp(self.__get_value(values, self.ColNr.VOLTOOIEN)),
                        titel = self.__get_value(values, self.ColNr.TITEL),
                        )
    def create_file(self, values: dict[str, Any])->str:
        merge_dict = {field: str(value.get(self.find_merge_field_vraag(field), '?')) 
                      for field in merge_fields}
        naam = self.__get_value(values, self.ColNr.NAAM)
        datum = self.__get_value(values, self.ColNr.VOLTOOIEN)
        bedrijf = self.__get_value(values, self.ColNr.BEDRIJF)
        filename = f'2. Aanvraag Afstuderen {datum}: {naam} {bedrijf}.docx'
        with MailMerge(self.template) as document:
            document.merge(**merge_dict)
            document.write(filename)
        return filename
    def create_directry
    pdf_file_name = str(path_with_suffix(docname, '.pdf'))
        Word2PdfConvertor().convert(docname, pdf_file_name)        

    reader = ExcelReader(filename, ENQUETE_COLUMNS)
# mapper = BaseDirExcelMapper()
if reader.error:
    print(reader.error)
else:
    with MailMerge(template) as document:
        merge_fields = document.get_merge_fields().copy()
    for n,value in enumerate(reader.read()):
        merge_dict = {field: str(value.get(find_merge_field_vraag(field, reader.columns), '?')) 
                      for field in merge_fields}
        with MailMerge(template) as document:
            document.merge(**merge_dict)
            docname = /f'{value.get('Naam')}.docx'
            document.write(docname)
        pdf_file_name = str(path_with_suffix(docname, '.pdf'))
        Word2PdfConvertor().convert(docname, pdf_file_name)