from pathlib import Path
import re
from data.classes.files import File
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.storage import AAPAStorage
from process.general.aanvraag_processor import VerslagCreator
from process.scan.importing.filename_parser import FilenameParser

class VerslagParseException(Exception): pass

class VerslagFromZipParser(VerslagCreator):
    def __init__(self, description = ''):
        super().__init__(description=description)
        self.parser = FilenameParser()

    def create_from_parsed(self, filename: str, parsed: FilenameParser.Parsed)->Verslag:
        VerslagTypes = {'plan van aanpak': Milestone.Type.PVA, 
                        'onderzoeksverslag': Milestone.Type.ONDERZOEKS_VERSLAG, 
                        'technisch verslag': Milestone.Type.TECHNISCH_VERSLAG, 
                        'eindverslag': Milestone.Type.EIND_VERSLAG}
        def get_verslag_type(product_type: str)->Milestone.Type:
            if (result := VerslagTypes.get(product_type.lower(), None)):
                return result
            raise VerslagParseException(f'Onbekend verslagtype: {[product_type]}')
        def get_kans(kans_decription: str)->int:
            KANSPATTERN = '(?<n>[\d]+).*kans'
            match kans_decription:
                case '1e kans': return 1
                case 'herkansing': return 2
                case re.match(KANSPATTERN, kans_decription):
                    return re.match(KANSPATTERN).group('n')
                case _: return 0
        return Verslag(verslag_type=get_verslag_type(parsed.product_type), student=Student(parsed.student_name, email=parsed.email), 
                       file=File(filename), datum=parsed.datum, kans=get_kans(parsed.kans), titel=Path(parsed.original_filename).stem)  
    def process_file(self, filename: str, storage: AAPAStorage, preview=False, **kwargs)->Verslag:
        if parsed:=self.parser.parsed(filename):
            new_filename = f'temp_placeholder {parsed.original_filename}'
            return self.create_from_parsed(new_filename, parsed)
        return None
