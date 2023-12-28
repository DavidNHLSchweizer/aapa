
from enum import Enum
from pathlib import Path
from typing import Any

from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.storage.aapa_storage import AAPAStorage

from general.config import config
from general.fileutil import created_directory, path_with_suffix, test_directory_exists
from general.log import log_info, log_print
from general.strutil import replace_all
from general.timeutil import TSC
from process.general.student_dir_builder import StudentDirectoryBuilder
from process.general.word_processor import Word2PdfConvertor
from process.scan.importing.excel_reader import ExcelReader




#     reader = ExcelReader(filename, ENQUETE_COLUMNS)
# # mapper = BaseDirExcelMapper()
# if reader.error:
#     print(reader.error)
# else:
#     with MailMerge(template) as document:
#         merge_fields = document.get_merge_fields().copy()
#     for n,value in enumerate(reader.read()):
#         merge_dict = {field: str(value.get(find_merge_field_vraag(field, reader.columns), '?')) 
#                       for field in merge_fields}
#         with MailMerge(template) as document:
#             document.merge(**merge_dict)
#             docname = /f'{value.get('Naam')}.docx'
#             document.write(docname)
#         pdf_file_name = str(path_with_suffix(docname, '.pdf'))
#         Word2PdfConvertor().convert(docname, pdf_file_name)