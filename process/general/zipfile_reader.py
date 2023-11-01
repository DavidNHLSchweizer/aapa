import datetime
import os
from pathlib import Path
from typing import Tuple
from zipfile import ZipFile

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
    def read_info(self, zip_filename: str):
        with ZipFile(zip_filename) as zipfile:
            self._files_in_zip.extend([{'zip': zip_filename, 'filename': zi.filename, 'info': zi} 
                                       for zi in zipfile.infolist() if Path(zi.filename).suffix != '.txt'])
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
