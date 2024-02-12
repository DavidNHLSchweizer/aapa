from argparse import ArgumentParser
from main.log import init_logging, log_info
from plugins.plugin import PluginRunner

if __name__ == "__main__":   
    def _get_modules():
        def _usage_str()->str:
            lines = [ '%(prog)s module [opties].',
                     'Modules: 1 of meer geldige plugins',
                     'Opties: alle opties die voor de module zijn gedefinieerd en alle opties die in AAPA mogelijk zijn.',
                     '\n',
                     'Meer informatie via run_plugin module -plugin_help',
            ]
            return "\n".join(lines)

        simple_parser = ArgumentParser(description='Script om (in principe) eenmalige acties uit te voeren voor AAPA.', 
                                       prog='run_plugin', usage=_usage_str())
        simple_parser.add_argument('modules', metavar='module(s)', nargs='*', type=str,
                            help='Module of modules om uit voeren.')
        simple_args,unknown_arguments = simple_parser.parse_known_args()
        modules = simple_args.__dict__.get('modules', [])
        if not modules:
            print('Geen modules ingevoerd.')
            exit(1)
        return (modules,unknown_arguments)
    (modules,arguments) = _get_modules()
    runner = PluginRunner(modules)
    if not runner:
        print(f'Kan module(s) {modules} niet initialiseren.')
        exit(1)
    runner.run(args=arguments)
        