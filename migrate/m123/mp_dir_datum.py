""" MP_DIR_DATUM

    Past de mijlpaal_directories aan door de datum in te stellen indien deze nog niet bestaat.

    De code is bedoeld voor de migratie naar database versie 1.23

"""
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.aapa_processor.aapa_processor import AAPARunnerContext


class MijlpalenDatumProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set datum=? where id=?'},}))                        
        return sql
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
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        processing_dict = self._get_mpd_data()
        for id,timestamp in processing_dict.items():
            self.set_timestamp(id, timestamp)
        return True