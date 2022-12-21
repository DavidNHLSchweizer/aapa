from pathlib import Path
import sys
import tkinter.messagebox as tkimb
import tkinter.filedialog as tkifd
from general.fileutil import path_with_suffix
from general.log import logInfo
from office.cleanup import cleanup_files
from office.graded_requests import process_graded
from general.config import config
from office.report_data import report_aanvragen_XLS, report_aanvragen_console
from process.database import initialize_database, initialize_storage
from process.requests import process_directory
from data.aanvraag_info import AanvraagBeoordeling
from general.args import AAPAoptions, Initialize, get_arguments, report_options

def init_config():
    config.set_default('configuration', 'database', 'aapa.db')
    config.set_default('configuration', 'root', r'.\aanvragen')
    config.set_default('configuration', 'forms', r'.\aanvragen\forms')
    config.set_default('configuration', 'mail', r'.\aanvragen\mail')
init_config()

def verifyRecreate():
    return tkimb.askyesno('Vraagje', 'Alle data wordt verwijderd. Is dat echt wat je wilt?', default = tkimb.NO, icon=tkimb.WARNING) 

class AAPA:
    def __init__(self, options: AAPAoptions):
        self.__initialize_database(options)
        self.__initialize_directories(options)
        logInfo(f'COMMAND LINE OPTIONS:\n{report_options(options)}')
        self.cleanup = options.clean
        self.noscan  = options.noscan
        self.nomail  = options.nomail
        self.report    = options.report
    def __initialize_database(self, options: AAPAoptions):
        recreate =  (options.initialize == Initialize.INIT and verifyRecreate()) or options.initialize == Initialize.INIT_FORCE
        if options.database:
            database = options.database
            config.set('configuration', 'database', database) 
        else:
            database = config.get('configuration','database') 
        self.database = initialize_database(database, recreate)
        self.storage  = initialize_storage(self.database)
    def __initialize_directories(self, options: AAPAoptions):        
        self.root = self.__get_directory(options.root, 'root','Root directory voor aanvragen', True)
        self.forms_directory = self.__get_directory(options.forms, 'forms', 'Directory voor beoordelingsformulieren')
        self.mail_directory = self.__get_directory(options.mail, 'mail', 'Directory voor mailbestanden')
    def __get_directory(self, option_value, config_name, title, mustexist=False):
        if option_value is not None and not option_value:
            result = tkifd.askdirectory(mustexist=mustexist, title=title)
        else:
            result = option_value
        if result and result != config.get('configuration', config_name):
            setattr(self, config_name, result)
            config.set('configuration', config_name, result)
        else:
            result = config.get('configuration', config_name)
        if result:
            return Path(result).resolve()
        else:
            return None
    def process(self):
        if not self.noscan and self.root:
            process_directory(self.root, self.storage, self.forms_directory)
        if not self.nomail and self.mail_directory:
            process_graded(self.storage, self.mail_directory)
        if self.cleanup:
            cleanup_files(self.storage)
        if self.report is not None:
            if self.report:
                report_aanvragen_XLS(self.storage, path_with_suffix(self.report, '.xlsx'))
            else:
                report_aanvragen_console(self.storage)
        logInfo('Ready.')
    @staticmethod
    def banner():
        return f'AAPA-Afstudeer Aanvragen Proces Applicatie  versie {config.get("versie", "versie")}'

if __name__=='__main__':
    print(AAPA.banner())
    AAPA(get_arguments()).process() 

#TODO rootify everything (involve "system root")