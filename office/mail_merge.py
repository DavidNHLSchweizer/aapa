from pathlib import Path
from mailmerge import MailMerge

from general.log import logError

class MailMerger:
    def __init__(self, output_directory: str):
        self.output_directory = Path(output_directory)
    def process(self, template_doc: str, output_file_name: str, **kwds)->str:
        try:
            full_output_name = self.output_directory.joinpath(output_file_name)
            document = MailMerge(template_doc)
            document.merge(**kwds)
            document.write(full_output_name)
            return Path(full_output_name).resolve()
        except Exception as E:
            logError(f'Error merging document (template:{template_doc}) to {full_output_name}: {E}')
            return None

