""" CORRECT_VERSLAGEN_DOUBLURES. 

    aanpassen van database voor dubbelingen in verslagen/kans in dezelfde mijlpaaldirectory.
    
    bedoeld voor migratie db naar versie 1.25
    
"""
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.verslagen import Verslag
from data.general.class_codes import ClassCodes
from database.classes.database import Database
from storage.queries.student_directories import StudentDirectoriesQueries
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class MijlpaalDirsReEngineeringProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('verslagen', SQLcollector({'delete': {'sql': 'delete from VERSLAGEN where id in (?)'},}))
        sql.add('verslagen_details', SQLcollector({'insert': {'sql':self.insert_detail_query('VERSLAGEN', 'verslag_id')},
                                                 'delete': {'sql':self.delete_detail_query('VERSLAGEN', 'verslag_id'), 'concatenate': False},}))
        return sql
    def _correct_verslag(self, verslag_correct_id: int, verslag_id: int, file_id: int):
        self.sql.delete('verslagen', [verslag_id])
        self.sql.delete('verslagen_details', [verslag_id, file_id, self.file_code])
        self.sql.delete('verslagen_details', [verslag_correct_id, file_id,self.file_code])# to be sure
        self.sql.insert('verslagen_details', [verslag_correct_id, file_id,self.file_code])        
    def _correct_directory(self, mp_dir: MijlpaalDirectory, entries: list[dict]):
        self.log(f'Correcting {File.display_file(mp_dir.directory)}')
        for entry in entries: 
            verslag_correct_id = None
            verslag_id,v_kans,_,file_id = entry.values()
            if v_kans == mp_dir.kans:
                verslag_correct_id = verslag_id
                break
        for entry in entries:
            verslag_id,v_kans,_,file_id = entry.values()
            if verslag_id != verslag_correct_id:
                self._correct_verslag(verslag_correct_id, verslag_id, file_id)
    def process_double_entry(self, mp_dir_id: int, entries: list[dict]):
        mp_dir = self.storage.read('mijlpaal_directories', mp_dir_id)        
        self._correct_directory(mp_dir, entries)
    def _get_double_entries(self)->dict:
        query = 'select V.ID, V.stud_id, V.kans as v_kans, MPD.kans as mpd_kans, MPD.id as mpd_id, MPD.directory,F.ID as file_id,F.Filename \
from VERSLAGEN as V inner join VERSLAGEN_DETAILS as VF on V.id = VF.verslag_id \
inner join FILES as F on VF.detail_id=F.ID \
inner join MIJLPAAL_DIRECTORIES_DETAILS as MPDF on F.ID = MPDF.detail_id \
inner join MIJLPAAL_DIRECTORIES as MPD on MPD.id = MPDF.mp_dir_id \
where mpd.mijlpaal_type <> 1 and MPDF.class_code = "FL" \
and exists \
(select V2.ID from verslagen as V2 inner join VERSLAGEN_DETAILS as VF on V2.id = VF.verslag_id \
inner join FILES as F on VF.detail_id=F.ID \
inner join MIJLPAAL_DIRECTORIES_DETAILS as MPDF on F.ID = MPDF.detail_id \
inner join MIJLPAAL_DIRECTORIES as MPD2 on MPD2.id = MPDF.mp_dir_id  \
where V2.kans <> V.kans and MPD.ID = MPD2.ID and MPDF.class_code = "FL" and VF.class_code = "FL")'
        rows = self.database._execute_sql_command(query,[], True)
        cur_mpd_id = None
        double_entries = {}
        cur_entries = []
        new_entry = None
        for row in rows:
            mpd_id = row['mpd_id']
            new_entry = {'verslag_id': row['id'], 'v_kans': row['v_kans'], 'mpd_kans': row['mpd_kans'], 'file_id': row['file_id']}
            if not cur_mpd_id or cur_mpd_id == mpd_id:
                cur_entries.append(new_entry)
            if not cur_mpd_id:                
                cur_mpd_id = mpd_id
            elif mpd_id != cur_mpd_id:
                double_entries[cur_mpd_id] = cur_entries
                cur_mpd_id = mpd_id
                cur_entries = [new_entry]
        if new_entry:
            cur_entries.append(new_entry)
            double_entries[cur_mpd_id] = cur_entries
        return double_entries
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        # self.verslag_code = ClassCodes.classtype_to_code(Verslag)
        self.file_code = ClassCodes.classtype_to_code(File)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        double_entries = self._get_double_entries()
        for key, entries in double_entries.items():
            self.process_double_entry(key, entries)
        self.sql.execute_sql(self.database, True)
        return True
