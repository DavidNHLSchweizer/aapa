""" REUNITE_ORPHANS

    Corrigeert bestanden die ten onrechte niet in een mijlpaaldirectory zijn opgenomen.

    De code is bedoeld voor de migratie naar database versie 1.23

    De processor is even apart gehouden en kan ook als gewone plugin worden ingezet.
    You never know.

"""
from argparse import ArgumentParser
from data.general.roots import Roots
from general.sql_coll import SQLcollectors
from main.log import log_info
from migrate.migration_plugin import MigrationPlugin
from plugins.sync_basedir import BasedirSyncProcessor
from process.main.aapa_processor import AAPARunnerContext

class SyncBasedirProcessor(MigrationPlugin):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--basedir', nargs='+', action='append', type=str, help='De basisdirectory (of -directories) om te synchroniseren. Argument kan meerdere keren worden opgegeven.') 
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        def _unlistify(basedirs:list[list[str]])->list[str]:
            """ Converts basedirs arguments from argument parser to simple list of strings 
            
                action='append' produces every --basedir=xxx argument as [xxx],
                so we get [[xxx1],[xxx2]...]. This "unlists" this to a simple list of strings.

            """
            if not basedirs:
                return []
            return [as_list[0] for as_list in basedirs]
        self.processor = BasedirSyncProcessor(context.configuration.storage)
        self.basedirs = [Roots.decode_onedrive(bd) for bd in _unlistify(kwdargs.get('basedir'))]
        return super().before_process(context, **kwdargs)
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        log_info('Start running basedir-sync')
        self.processor.process(self.basedirs, context.preview, self.verbose)
        return True
    def init_SQLcollectors(self) -> SQLcollectors:
        return self.processor.sql_processor.sql
