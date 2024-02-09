""" M123_MP_DIR_DATUM

    Past de mijlpaal_directories aan door de datum in te stellen indien deze nog niet bestaat.

    De code is bedoeld voor de migratie naar database versie 1.23

"""
from argparse import ArgumentParser, Namespace
from data.storage.aapa_storage import AAPAStorage
from extra.tools import BaseMigrationProcessor
from general.preview import Preview
from general.timeutil import TSC
from general.sql_coll import SQLcollector, SQLcollectors
from process.aapa_processor.aapa_processor import AAPARunnerContext


class MijlpalenDatumProcessor(BaseMigrationProcessor):
    def __init__(self, storage: AAPAStorage, verbose=False):
        super().__init__(storage, verbose)
        self.sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set datum=? where id=?'},}))                        
    def set_timestamp(self, mp_id: int, timestamp: str):
        self.sql.update('mijlpaal_directories', [timestamp, mp_id])
    def _get_mpd_data(self)->dict:
        query = 'select MPD.id as mpd_id,F.timestamp from MIJLPAAL_DIRECTORIES MPD \
inner join MIJLPAAL_DIRECTORY_FILES as MPDF on MPD.ID=MPDF.mp_dir_id \
inner join FILES as F on MPDF.file_id=F.ID \
where MPD.datum is ? order by 1,2'
        database = self.storage.database
        rows = database._execute_sql_command(query, [""],True)
        result = {}
        prev_mpd_id = -1
        for row in rows:
            mpd_id = row['mpd_id']
            if mpd_id != prev_mpd_id:
                prev_mpd_id = mpd_id
                result[mpd_id] = row['timestamp']
            else:
                assert row['timestamp'] >= result[mpd_id]
        return result
    def processing(self):        
        processing_dict = self._get_mpd_data()
        for id,timestamp in processing_dict.items():
            self.set_timestamp(id, timestamp)
        
def extra_args(base_parser: ArgumentParser)->ArgumentParser:
    base_parser.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 
    base_parser.add_argument('-v', '--verbose', action="store_true", help='If true: logging gaat naar de console ipv het logbestand.')
    return base_parser

def extra_main(context:AAPARunnerContext, namespace: Namespace):
    context.processing_options.debug = True
    context.processing_options.preview = True
    migrate_dir=namespace.migrate if 'migrate' in namespace else None
    storage = context.configuration.storage
    with Preview(True,storage,'Update mijlpaal_directories datum (voor migratie)'):
        processor = MijlpalenDatumProcessor(storage,verbose=namespace.verbose)
        processor.process_all(module_name=__file__, migrate_dir=migrate_dir)        