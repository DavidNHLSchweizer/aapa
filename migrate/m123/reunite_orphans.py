""" REUNITE_ORPHANS

    Corrigeert bestanden die ten onrechte niet in een mijlpaaldirectory zijn opgenomen.

    De code is bedoeld voor de migratie naar database versie 1.23

    De processor is even apart gehouden en kan ook als gewone plugin worden ingezet.
    You never know.

"""
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from plugins.orphan_files import OrphanFileProcessor
from process.main.aapa_processor import AAPARunnerContext

class ReuniteOrphansProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('mijlpaal_directory_files', SQLcollector(
            {'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES (mp_dir_id,file_id) values(?,?)',}}))
        return sql
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        self.processor = OrphanFileProcessor(context.storage)
        self.processor.process(context.preview, self.sql)
        return True