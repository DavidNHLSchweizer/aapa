import sys
import tkinter.messagebox as tkimb
from office.graded_requests import process_graded
from general.config import config
from process.database import initialize_database, initialize_storage
from process.requests import process_directory

def init_config():
    config.set_default('general', 'version','0.7')
init_config()

class AAPA:
    def __init__(self, recreate = False):
        self.database = initialize_database(recreate)
        self.storage  = initialize_storage(self.database)
    def do_requests(self, input_directory: str, output_directory: str):
        process_directory(input_directory, self.storage, output_directory)
    def do_graded_requests(self, output_directory: str):
        process_graded(self.storage, output_directory)
    @staticmethod
    def banner():
        return f'AAPA-Afstudeer Aanvragen Proces Applicatie  versie {config.get("general", "version")}'

if __name__=='__main__':
    print(AAPA.banner())

    data = [r'C:\repos\aapa\week47', r'C:\repos\aapa\week48', r'C:\repos\aapa\week49', r'C:\repos\aapa\week50']

    def verifyRecreate():
        return tkimb.askyesno('Vraagje', 'Alle data wordt verwijderd. Is dat echt wat je wilt?', default = tkimb.NO, icon=tkimb.WARNING) 

    recreate = len(sys.argv) > 1  and sys.argv[1].lower() == '/r' and verifyRecreate()
    aapa = AAPA(recreate)
    if recreate:
        for d in data[0:4]:
            aapa.do_requests(d, r'.\new_requests')
    else:
        aapa.do_graded_requests(r'.\temp')
