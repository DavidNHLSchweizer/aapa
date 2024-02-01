from __future__ import annotations
from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import re
from typing import Tuple
from zipfile import ZipFile
from general.log import log_warning

from general.config import ListValueConvertor, config
from general.name_utils import Names

def init_config():
    config.register('zipfile', 'doc_suffix', ListValueConvertor)
    #dit kan worden aangepast als bv ODF ook geaccepteerd wordt.
    config.init('zipfile', 'doc_suffix', ['.docx', '.pdf'])    
init_config()

class BBException(Exception):pass

class BBFilenameInZipParser:
    @dataclass
    class Parsed:       
        filename_in_zip: str 
        product_type: str
        kans: str
        email: str
        datum: datetime.datetime
        original_filename: str
        submission_text = False
        @property
        def student_name(self)->str:
            words = []         
            for word in self.email[:self.email.find('@')].split('.'):
                if Names.is_tussen(word):
                    words.append(word)
                else:
                    words.append(word.title())
            return ' '.join(words)
    PATTERN1 = r'Inleveren\s+(?P<product_type>.+)\s+\((?P<kans>.+)\)_(?P<email>.+)_poging_(?P<datum>[\d\-]+)_(?P<filename>.+)'
    PATTERN2 = r'Inleveren\s+(?P<product_type>.+)\s+\((?P<kans>.+)\)_(?P<email>.+)_attempt_(?P<datum>[\d\-]+)_(?P<filename>.+)'
    PATTERN3 = r'Inleveren\s+(?P<product_type>.+)\s+\((?P<kans>.+)\)_(?P<email>.+)_poging_(?P<datum>[\d\-]).txt'
    PATTERN4 = r'Inleveren\s+(?P<product_type>.+)\s+\((?P<kans>.+)\)_(?P<email>.+)_attempt_(?P<datum>[\d\-]).txt'
    def __init__(self):
        self.pattern1 = re.compile(self.PATTERN1,re.IGNORECASE)
        self.pattern2 = re.compile(self.PATTERN2,re.IGNORECASE)
    def parsed(self, filename: str)->BBFilenameInZipParser.Parsed:
        if (match:=self.pattern1.match(str(filename))) or (match:=self.pattern2.match(str(filename))):
            return self.Parsed(filename_in_zip=filename, product_type=match.group('product_type'), kans=match.group('kans'), 
                                  email=match.group('email'), 
                                  datum=datetime.datetime.strptime(match.group('datum'),'%Y-%m-%d-%H-%M-%S'),
                                  original_filename=match.group('filename'))
        return None

class ZipFileReader:
    def __init__(self):
        self._files_in_zip: list[dict] = []
    @property
    def filenames(self)->list[str]:
        return [entry['filename'] for entry in self._files_in_zip]
    def _get_filename_entry(self, filename: str)->dict:
        for entry in self._files_in_zip:
            if entry['filename']==filename:
                return entry
        return None
    def read_info(self, zip_filename: str, reset=True):
        if reset:
            self._files_in_zip: list[dict] = []
        with ZipFile(zip_filename) as zipfile:            
            self._files_in_zip.extend([{'zip': zip_filename, 'filename': zi.filename, 'info': zi} 
                                       for zi in zipfile.infolist()])
    def extract_file(self, filename: str, path: str = None, dest_name: str = None)->str:
        def _restore_file_time(filename: Path, date_time_in_info: Tuple[int,int,int,int,int,int]):
            original_date = datetime.datetime(*date_time_in_info).timestamp()
            os.utime(filename,(original_date, original_date))
        def _check_rename(filename: Path, new_name: str)->str:
            if new_name: 
                return str(filename.replace(new_name))
            return str(filename)
        if entry:=self._get_filename_entry(filename):
            with ZipFile(entry['zip']) as zipfile:
                zipfile.extract(entry['filename'], path=path)
                _restore_file_time(entry['filename'], entry['info'].date_time)
                return _check_rename(Path(path).joinpath(entry['filename']) if path else Path(entry['filename']), dest_name)
        return None

class BBZipFileReader(ZipFileReader):
    def __init__(self):
        self.parser= BBFilenameInZipParser()
        self._parsed_list: list[BBFilenameInZipParser.Parsed] = []
        super().__init__()    
    @property
    def parsed_list(self)->list[BBFilenameInZipParser.Parsed]:
        return self._parsed_list        
    def _filenames(self, suffix: list[str])->list[str]:
        return list(filter(lambda fn: Path(fn).suffix in suffix,self.filenames))    
    def parse(self, zip_filename: str, reset=True):
        if reset:
            self._parsed_list = []
        self.read_info(zip_filename, reset)
        txts:list[str] = self._filenames(['.txt'])
        doc_suffixes = config.get('zipfile', 'doc_suffix')
        for parsed_file in [self.parser.parsed(filename_in_zip) for filename_in_zip in self._filenames(doc_suffixes)]:            
            txt_filename = f"{parsed_file.filename_in_zip[:-(len(parsed_file.original_filename)+1)]}.txt"
            if txt_filename in txts:
                parsed_file.original_filename = self._find_original_path(zip_filename, txt_filename, parsed_file.filename_in_zip)
            else:
                log_warning(f'Assignment bestand {txt_filename} niet gevonden in {zip_filename}.\nHierdoor kan de oorspronkelijke bestandnaam mogelijk niet worden gereconstrueerd.')
            self._parsed_list.append(parsed_file)
    def _find_original_files(self, zip_filename: str, txt_filename: str)->dict:
        #dit moet omdat Blackboard bestandsnamen soms op onduidelijke manier verhaspelt
        #in de assignment file (.txt) staat echter de correcte originele filename
        #deze methode leest de assignment file en geeft een dict terug met daarin de koppeling met de originele filenaam 
        PATTERN1 = rf'.*Original filename: (?P<original_filename>.*)\n' #de "echte" filenaam
        PATTERN2 = rf'.*Filename: (?P<filename>.*)\n' #de filenaam zoals in de zip, soms met vreemde hex-tekens er in
        filenames = []
        original_filenames = []
        with ZipFile(zip_filename) as zipfile:  
            pattern1 = re.compile(PATTERN1,re.IGNORECASE)
            pattern2 = re.compile(PATTERN2,re.IGNORECASE)
            for line in zipfile.open(txt_filename):
                if match:=pattern1.match(str(line, 'utf-8')):
                    original_filenames.append(match.group('original_filename'))
                elif match:=pattern2.match(str(line, 'utf-8')):
                    filenames.append(match.group('filename'))
        return {filename: original_filename for (filename,original_filename) in zip(filenames,original_filenames)}
    def _find_original_path(self, zip_filename: str, txt_filename: str, filename_in_zip: str)->str:
        return self._find_original_files(zip_filename, txt_filename).get(filename_in_zip,filename_in_zip)
