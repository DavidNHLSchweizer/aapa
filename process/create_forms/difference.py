import difflib
import html
from pathlib import Path

from process.importing.import_data import PDFaanvraagReader

class DifferenceGenerator:
    def __init__(self, version1, version2: str):
        self.table_lines1 = PDFaanvraagReader(version1).all_lines()
        self.table_lines2 = PDFaanvraagReader(version2).all_lines()
        self.version1 = version1
        self.version2 = version2
        self.html_differ = difflib.HtmlDiff()
    def generate_html(self, html_file: str, context=False):
        def diff_column_header(msg, filename):
            return html.escape(f'({msg}) {Path(filename).name}')
        with open(html_file, "w", encoding='utf8') as file:
            file.write(self.html_differ.make_file(self.table_lines1, self.table_lines2, 
                            fromdesc=diff_column_header('oud', self.version1), 
                            todesc=diff_column_header('nieuw', self.version2), 
                            context=context))

def create_difference_file(version1, version2, difference_filename, preview=False):
    if not preview:
        DifferenceGenerator(version1, version2).generate_html(difference_filename)
    aangemaakt = 'aan te maken' if preview else 'aangemaakt'
    print(f'Verschil-bestand {difference_filename} {aangemaakt} van deze versie ({version2}) met vorige versie ({version1})')

        