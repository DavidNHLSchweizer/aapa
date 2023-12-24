
from typing import Iterable
from mailmerge import MailMerge

from general.fileutil import path_with_suffix
from process.general.word_processor import Word2PdfConvertor
from process.scan.importing.excel_reader import ExcelReader

filename = r'd:\aapa\test_aanvragen.xlsx'
template = r'd:\aapa\templates\2. Aanvraag goedkeuring afstudeeropdracht nieuwe vorm MAILMERGE.docx'

ENQUETE_COLUMNS= \
    ['ID', 'Begintijd', 'Tijd van voltooien', 'E-mail', 'Naam',
       'Tijd van laatste wijziging', 'Wat is je studentnummer',
       'Wat is je telefoonnummer', 'Hoe ga je afstuderen?',
       'Bij welk bedrijf ga je afstuderen?',
       'Wat is het adres van het afstudeerbedrijf?',
       'Wat is de website van het bedrijf?',
       'Wat is de naam van je bedrijfsbegeleider?',
       'Wat is de functie van deze bedrijfsbegeleider?',
       'Wat is het e-mail adres van deze bedrijfsbegeleider',
       'Wat is het telefoonnummer van deze bedrijfsbegeleider',
       'Hoe heb je deze opdracht gevonden?',
       'Wanneer wil je starten met je afstudeeropdracht?',
       'Kerntaken van het bedrijf',
       'Wat is het belang voor de opdrachtgever bij deze opdracht?',
       'Begeleiding',
       '(Voorlopige, maar beschrijvende) Titel van de afstudeeropdracht',
       'Wat is de aanleiding voor de opdracht? \n',
       'Korte omschrijving van de opdracht\n',
       'Wat zijn de op te leveren beroepsproducten uit jouw project?\n ',
       'Wat zijn de op te leveren softwareproduct(en) uit jouw project? \n',
       'Onderzoekend vermogen: welke ruimte is er in de opdracht om zaken te onderzoeken? \n ',
       'Analysefase: Hoe kom je aan de (functionele/non functionele) requirements? \n',
       'Ontwerpfase: Hoe ga je ontwerpen (werkwijze, methode) en wat ontwerp je (voorlopig)?',
       'Testfase: hoe kun je de kwaliteit van je softwareproduct aantonen? \n',
       'Kwaliteitsbewaking: welke processen ga je inzetten om grip te houden op je kwaliteit en voortgang?\n ',
       'Welke technieken/frameworks ga je inzetten en welke hiervan heb je nog geen ervaring mee. \n']

# with MailMerge(template) as document:
#     merge_fields = document.get_merge_fields()
# for field in merge_fields:
#     print(field)

# print('-------')

def replace_all(s: str, replace_chars: str, replace_with: str)->str:
    result = s
    for c in replace_chars:
        result = result.replace(c, replace_with)
    return result
 
def _standardize_vraag(vraag: str)->str:
    return replace_all(replace_all(vraag, ':/(),-', ''), ' ?\n', '_').replace('___', '__')

def match_enquete_vraag(vraag: str, merge_fields: str)->str:
    vraag2 = _standardize_vraag(vraag)
    for field in merge_fields:
        if vraag2.find(field) == 0:
            return field
    return None

def find_merge_field_vraag(merge_field: str, vragen: Iterable[str])->str:
    for vraag in vragen:
        vraag2 = _standardize_vraag(vraag)
        if vraag2.find(merge_field)==0:
            return vraag
    return 'not found'

# print('#---------')
# for field in merge_fields:
#     print(find_merge_field_vraag(field, ENQUETE_COLUMNS))

print('---------')



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
            docname = f'{value.get('Naam')}.docx'
            document.write(docname)
        pdf_file_name = str(path_with_suffix(docname, '.pdf'))
        Word2PdfConvertor().convert(docname, pdf_file_name)