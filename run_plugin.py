from argparse import SUPPRESS, ArgumentParser
from main.log import init_logging, log_info
from plugins.plugin import PluginException, PluginRunner

# use this as first argument to signal the end of the modules
# stop will be ignored.
STOP = '-stop'

if __name__ == "__main__":   

    def _get_modules():
        def _usage_str()->str:
            lines = [ '%(prog)s modules [opties].',
                     'Modules: 1 of meer geldige plugins',
                     'Opties: alle opties die voor de module zijn gedefinieerd en alle opties die in AAPA mogelijk zijn.',
                     '\n',
                     'Meer informatie via run_plugin module -plugin_help',
            ]
            return "\n".join(lines)

        simple_parser = ArgumentParser(description='Script om (in principe) eenmalige acties uit te voeren voor AAPA.', 
                                       prog='run_plugin', usage=_usage_str(), fromfile_prefix_chars='@')
        simple_parser.add_argument('modules', metavar='module(s)', nargs='*', type=str,
                            help='Module of modules om uit voeren.')
        simple_args,unknown_arguments = simple_parser.parse_known_args()
        if unknown_arguments[0] == STOP:
            unknown_arguments.remove(STOP)
        modules:list[str] = simple_args.__dict__.get('modules', [])
        if not modules:
            print('Geen modules ingevoerd.')
            exit(1)
        return (modules,unknown_arguments)
    try:
        (modules,arguments) = _get_modules()
        runner = PluginRunner(modules)
        if not runner:
            print(f'Kan module(s) {modules} niet initialiseren.')
            exit(1)
        runner.run(args=arguments)
    except Exception as E:
        print(f'Error running plugin: {E}')

        