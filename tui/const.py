from general.args import AAPAConfigOptions, AAPAOptions, AAPAOtherOptions, AAPAProcessingOptions, AAPAaction, ArgumentOption, get_options_from_commandline


MISSINGHELP = 'Help helaas niet ingevoerd...'

ToolTips = {'config': 
                {'root': 'De root-directory waar de studenten van een bepaald jaarcohort worden opgeslagen',
                'output': 'De directory waar beoordelingsformulieren worden aangemaakt voor aanvragen',
                'input': 'Kies (excel) input bestand met nieuwe aanvragen (optioneel)',
                'bbinput': 'De directory waar uit Blackboard afkomstige .ZIP-files worden gevonden',
                'scanroot': 'De directory waarbinnen gezocht wordt naar (nieuwe) aanvragen', 
                'database':'De database voor het programma',
                'root-input-button': 'Kies de root-directory',
                'output-input-button': 'Kies de output-directory',
                'database-input-button': 'Kies de database',
                'scanroot-input-button': 'Kies de directory waarbinnen gezocht wordt naar (nieuwe) aanvragen', 
                'bbinput-input-button': 'Kies de Blackboard Input directory',
                'input-input-button': 'Kies input bestand',
                'input-switch': 'Lees aanvragen uit de Excel-inputfile',
                'scanroot-switch': 'Scan aanvraagbestanden',
                'bbinput-switch': 'Importeer verslagen uit Blackboard-zipbestanden',
                },
            'processing':
                {
                'mode_aanvragen': 'Verwerk aanvragen',
                'mode_rapporten': 'Verwerk rapporten',
                'mode_preview': 'Laat verloop van de acties zien; Geen wijzigingen in bestanden of database.',
                'mode_uitvoeren': 'Voer acties uit. Wijzigingen in bestanden en database.',
                },
            'buttons':
                {'scan': 'Importeer data volgens Input Options (aanvragen in Excel en/of root-directory/subdirectories en/of rapporten in Blackboard .ZIP-file)',
                'form': 'Maak aanvraagformulieren',
                'mail': 'Zet mails klaar voor beoordeelde aanvragen',
                'undo': 'Maak de laatste actie (scan,form of mail) ongedaan',
                'report': 'Schrijf alle aanvragen in de detabase naar een Excel-bestand',
                },
            }

class AAPATuiParams:
    def __init__(self, root_directory: str = '', output_directory: str = '', database: str = '', excel_in: str = '',
                 bbinput_directory: str = '', preview: bool = True, input_options: set[AAPAProcessingOptions.INPUTOPTIONS] = set()):
        self.root_directory = root_directory
        self.output_directory = output_directory
        self.database = database
        self.excel_in = excel_in
        self.bbinput_directory = bbinput_directory
        self.preview=preview
        self.input_options = input_options
    def get_options(self, action: AAPAaction, report_filename = '')->AAPAOptions:
        def _get_config_options(report_filename: str)->AAPAConfigOptions:
            result = get_options_from_commandline(ArgumentOption.CONFIG)
            result.root_directory=self.root_directory
            result.output_directory=self.output_directory
            result.database_file=self.database
            result.report_filename=report_filename
            result.excel_in = self.excel_in
            return result
        def _get_processing_options(action: AAPAaction)->AAPAProcessingOptions:
            result = get_options_from_commandline(ArgumentOption.PROCES)
            result.actions=[action]
            result.preview=self.preview
            result.input_options = self.input_options
            return result
        def _get_other_options()->AAPAOtherOptions:
            return get_options_from_commandline(ArgumentOption.OTHER) 
        return AAPAOptions(config_options=_get_config_options(report_filename),
                           processing_options=_get_processing_options(action),
                           other_options=_get_other_options())

def windows_style(path: str)->str:
    #because askdirectory/askfile returns a Posix-style path which causes trouble
    if path:
        return path.replace('/', '\\')
    return ''
