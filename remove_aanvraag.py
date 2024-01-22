
from argparse import ArgumentParser
from general.args import _copy_parser, _get_options_from_commandline, get_options_from_commandline
from migrate.remover import AanvraagRemover
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.aapa_processor.aapa_processor import AAPARunnerContext

if __name__ == "__main__":
    extra_parser = ArgumentParser(description='script om aanvragen te verwijderen', prog='remove_aanvraag', usage='%(prog)s [actie(s)] [opties]')
    _copy_parser(extra_parser)
    extra_parser.add_argument('--aanvraag', nargs='+', help='Aanvraag id(s) om te verwijderen')
    args = extra_parser.parse_args()   
    coded_list:str = args.aanvraag[0]
    if ',' in coded_list:
        aanvragen = [int(id) for id in coded_list.split(',')]
    else:
        aanvragen = [int(id) for id in coded_list.split()]

    (config_options, processing_options, other_options) = _get_options_from_commandline(args)
    with AAPARunnerContext(AAPAConfiguration(config_options), processing_options, other_options) as context:
        storage = context.configuration.storage
        remover = AanvraagRemover(storage)
        remover.remove(aanvragen, processing_options.preview)
