import logging
from pathlib import Path
from mailmerge import MailMerge

from general.log import logError

class MailMerger:
    def __init__(self, template_doc: str, output_directory: str):
        self.template_doc = template_doc
        self.output_directory = Path(output_directory)
    def process(self, output_file_name: str, **kwds)->str:
        try:
            full_output_name = self.output_directory.joinpath(output_file_name)
            document = MailMerge(self.template_doc)
            document.merge(**kwds)
            document.write(full_output_name)
            return Path(full_output_name).resolve()
        except Exception as E:
            logError(f'Error merging document (template:{self.template_doc}) to {full_output_name}: {E}')
            return None

