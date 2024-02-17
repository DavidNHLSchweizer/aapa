from __future__ import annotations
from dataclasses import dataclass
import shutil
from tempfile import TemporaryDirectory
import datetime
import os
from pathlib import Path
import re
from typing import Tuple
from zipfile import ZipFile, ZipInfo
from general.fileutil import created_directory, set_file_time, test_directory_exists
from main.log import log_warning

from main.config import ListValueConvertor, config
from general.name_utils import Names

def init_config():
    config.register('zipfile', 'doc_suffix', ListValueConvertor)
    #dit kan worden aangepast als bv ODF ook geaccepteerd wordt.
    config.init('zipfile', 'doc_suffix', ['.docx', '.pdf'])    
init_config()

class BBException(Exception):pass

#note: combined path length of filename and path can not exceed 259 (limitation of Win machines)
WINDOWS_MAX_ZIPFILE_PATHLEN = 259

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
    @dataclass
    class FileInfo:
        zip_filename: str
        filename: str
        original_filename: str
        info: ZipFile.ZipInfo = None
    def __init__(self):
        self._files_in_zip: list[ZipFileReader.FileInfo] = []
    @property
    def filenames(self)->list[str]:
        return [entry.filename for entry in self._files_in_zip]
    def _get_filename_entry(self, filename: str)->ZipFileReader.FileInfo:
        for entry in self._files_in_zip:
            if entry.filename==filename:
                return entry
        return None
    def read_info(self, zip_filename: str, reset=True):
        if reset:
            self._files_in_zip: list[dict] = []
        with ZipFile(zip_filename) as zipfile:            
            self._files_in_zip.extend([ZipFileReader.FileInfo(zip_filename=zip_filename, filename=zi.filename, original_filename = zi.orig_filename, info=zi)
                                       for zi in zipfile.infolist()])
    def _safe_extract(self, entry: ZipFileReader.FileInfo, destination_path: str|Path, destination_name: str|Path)->str:
        with TemporaryDirectory() as tmp, ZipFile(entry.zip_filename) as zipfile:
            extracted_file = Path(zipfile.extract(entry.filename, tmp))
            if not (test_directory_exists(destination_path) or created_directory(destination_path)):
                raise BBException(f'Can not extract to directory {destination_path}')
            if not destination_path:
                destination_path = Path('.').resolve()
            if not destination_name:
                destination_name = extracted_file.name
            destination_filename = Path(destination_path).joinpath(destination_name) 
            if extracted_file.drive == Path(destination_filename).drive:
                new_path = Path(extracted_file).replace(destination_filename)
            else:
                new_path = shutil.copy2(extracted_file, destination_filename)
        return new_path
    def extract_file(self, filename_in_zip: Path|str, path: Path|str=None, destination_name: Path|str=None)->str:
        CANNOTBEEXTRACTED = 'Can not be extracted.'
        def _restore_file_time(filename: Path, date_time_in_info: Tuple[int,int,int,int,int,int]):
            set_file_time(filename, datetime.datetime(*date_time_in_info))
        if entry:=self._get_filename_entry(filename_in_zip):
            if len(filename_in_zip) >= WINDOWS_MAX_ZIPFILE_PATHLEN:
                raise BBException(f'Filename in zip is too long {entry["filename"]}.\n\tMaximum is {WINDOWS_MAX_ZIPFILE_PATHLEN}. {CANNOTBEEXTRACTED}')
            extracted_file = self._safe_extract(entry, path, destination_name)
            _restore_file_time(extracted_file,entry.info.date_time)
            return extracted_file
        return ''

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
        ori_names = ['Original filename', 'Oorspronkelijke bestandsnaam']
        def get_pattern1(ori_name: str)->str:
            return rf'.*{ori_name}: (?P<original_filename>.*)\n' #de "echte" filenaam
        def get_pattern2(ori_name: str)->str:
            name = ori_name.split()[-1]
            return rf'.*{name}: (?P<filename>.*)\n' #de filenaam zoals in de zip, soms met vreemde hex-tekens er in

        filenames = []
        original_filenames = []
        with ZipFile(zip_filename) as zipfile:  
            for ori_name in ori_names:
                pattern1 = re.compile(get_pattern1(ori_name),re.IGNORECASE)
                pattern2 = re.compile(get_pattern2(ori_name),re.IGNORECASE)
                for line in zipfile.open(txt_filename):
                    if match:=pattern1.match(str(line, 'utf-8')):
                        original_filenames.append(match.group('original_filename'))
                    elif match:=pattern2.match(str(line, 'utf-8')):
                        filenames.append(match.group('filename'))
        return {filename: original_filename for (filename,original_filename) in zip(filenames,original_filenames)}
    def _find_original_path(self, zip_filename: str, txt_filename: str, filename_in_zip: str)->str:
        return self._find_original_files(zip_filename, txt_filename).get(filename_in_zip,filename_in_zip)
    