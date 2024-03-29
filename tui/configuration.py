from textual.app import ComposeResult
from textual.widgets import Static, Button, Switch, TabbedContent, TabPane, Input
from main.options import AAPAProcessingOptions, ArgumentOption, get_options_from_commandline

from main.config import config
from tui.general.labeled_input import LabeledInput
from tui.general.utils import Required
from tui.general.utils import id2selector
from tui.common import BASE_CSS, MISSINGHELP, AAPATuiParams, ToolTips, windows_style
import tkinter.filedialog as tkifd

class AapaConfigurationForm(Static):
    DEFAULT_CSS = BASE_CSS + """
        AapaConfigurationForm {
            height: 18;
            background: $background;
            margin: 0;
            border: round $border;
        }
        AapaConfigurationForm LabeledInput {
            margin: 0 0 0 1;
        }
        AapaConfigurationForm LabeledInput Label {
            color: black;
        }
        AapaConfigurationForm LabeledInput Input:focus {
            outline: double black;
        }
        AapaConfigurationForm LabeledInput Input {
            outline: solid black;
        }
        AapaConfigurationForm .small {
            color: blue;
            background: darkgoldenrod;
        }
        AapaConfigurationForm LabeledSwitchGroup{
            height: 4;
        }
    """
    scrolled = False
    def __init__(self):
        self._processing_mode = AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN
        self._config_ids = ['root', 'output', 'input', 'scanroot', 'bbinput', 'database']
        super().__init__()
    def compose(self)->ComposeResult:
        with TabbedContent():
            with TabPane('input', id='input_tab'):
                yield LabeledInput('Importeer aanvragen uit MS-Forms Excel file:', id='input', button=True, switch=True)
                yield LabeledInput('Importeer aanvragen (PDF-files) uit directory:', id='scanroot', button=True, switch=True)
                yield LabeledInput('Importeer verslagen uit Blackboard (ZIP-files) in directory:', id='bbinput', validators=Required(), button=True)
            with TabPane('output', id='output_tab'):
                yield LabeledInput('Output directory', id='output', validators=Required(), button=True)
            with TabPane('basisconfiguratie', id='base_tab'):
                yield LabeledInput('Root directory', id='root', validators=Required(), button=True)
                yield LabeledInput('Database', id='database', validators=Required(), button=True)                
    def on_mount(self):
        tooltips = ToolTips.get('config', {})
        self.border_title = 'Configuratie'
        for id in self._config_ids:
            self.query_one(id2selector(id), LabeledInput).input.tooltip = tooltips.get(id, MISSINGHELP)
        for id in [f'{id}-input-button' for id in self._config_ids]:
            self.query_one(id2selector(id), Button).tooltip = tooltips.get(id, MISSINGHELP)
        for id in ['scanroot-switch', 'input-switch']:
            self.query_one(id2selector(id), Switch).tooltip = tooltips.get(id, MISSINGHELP)
        self._load_config()
        self.input_options = self._get_input_options()
        self.enable_all()
    def _load_config(self):        
        for id in self._config_ids:
            self.query_one(id2selector(id), LabeledInput).value = config.get('configuration', id)
    def _store_config_id(self, id: str):        
        config.set('configuration', id, self.query_one(id2selector(id), LabeledInput).value)
    def _store_config(self):
        for id in self._config_ids:
            self._store_config_id(id)
    def _select_directory(self, input_id: str, title: str):
        input = self.query_one(id2selector(input_id), LabeledInput).input
        if (result := windows_style(tkifd.askdirectory(mustexist=True, title=title, initialdir=input.value))):
            input.value=result
            input.cursor_position = len(result)
            input.focus()
    def _select_file(self, input_id: str, title: str, default_file: str, default_extension: str, for_open: bool = False):
        input = self.query_one(id2selector(input_id), LabeledInput).input
        if for_open:
            result = windows_style(tkifd.askopenfilename(initialfile=input.value, title=title, 
                                            filetypes=[(default_file, f'*{default_extension}'),('all files', '*')], defaultextension=default_extension))
        else:
            result = windows_style(tkifd.asksaveasfilename(initialfile=input.value, title=title, confirmoverwrite = False,
                                            filetypes=[(default_file, f'*{default_extension}'),('all files', '*')], defaultextension=default_extension))
        if result:
            input.value=result
            input.cursor_position = len(result)
            input.focus()
    def on_input_changed(self, message:Input.Changed):
        id_map = {f'{id}-input-input':id for id in self._config_ids}
        if message.input.id in id_map.keys():
            self._store_config_id(id_map[message.input.id])
    def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case 'root-input-button': self.edit_root()
            case 'output-input-button': self.edit_output_directory()
            case 'database-input-button': self.edit_database()
            case 'scanroot-input-button': self.edit_scanroot()
            case 'bbinput-input-button': self.edit_bbinput_directory()
            case 'input-input-button': self.edit_inputfile()
        message.stop()
    def edit_root(self):
        self._select_directory('root', 'Selecteer root directory voor studenten)')
    def edit_scanroot(self):
        self._select_directory('scanroot', 'Selecteer root directory voor scannen nieuwe aanvragen)')
    def edit_output_directory(self):
        self._select_directory('output', 'Selecteer de output directory voor nieuwe formulieren')
    def edit_bbinput_directory(self):
        self._select_directory('bbinput', 'Selecteer directory voor Blackboard .ZIP-files)')
    def edit_database(self):
        self._select_file('database','Select databasefile', 'database files', '.db')
    def edit_inputfile(self):
        self._select_file('input','Select inputfile', 'excel files', '.xlsx')
    @property
    def params(self)-> AAPATuiParams:
        return AAPATuiParams(root_directory= self.query_one(id2selector('root'), LabeledInput).input.value, 
                            bbinput_directory= self.query_one(id2selector('bbinput'), LabeledInput).input.value,
                             output_directory= self.query_one(id2selector('output'), LabeledInput).input.value,
                             database=self.query_one(id2selector('database'), LabeledInput).input.value,
                             excel_in = self.query_one(id2selector('input'), LabeledInput).input.value
                             )
    @property
    def input_options(self)->set[AAPAProcessingOptions.INPUTOPTIONS]:
        trans_dict = {'input-switch': AAPAProcessingOptions.INPUTOPTIONS.EXCEL,
                      'scanroot-switch': AAPAProcessingOptions.INPUTOPTIONS.SCAN, 
                      }
        result = set()
        for key in trans_dict.keys():
            value = self.query_one(id2selector(key), Switch).value
            if value:
                result.add(trans_dict[key])
        return self._match_options_to_processing_mode(result)
    @input_options.setter
    def input_options(self, value: set[AAPAProcessingOptions.INPUTOPTIONS]):
        trans_dict = {AAPAProcessingOptions.INPUTOPTIONS.EXCEL: 'input-switch',
                       AAPAProcessingOptions.INPUTOPTIONS.SCAN: 'scanroot-switch', 
                      }
        value = self._match_options_to_processing_mode(value)
        for option in {AAPAProcessingOptions.INPUTOPTIONS.EXCEL, AAPAProcessingOptions.INPUTOPTIONS.SCAN}:
             switch = self.query_one(id2selector(trans_dict[option]), Switch)
             switch.value = option in value
    def _match_options_to_processing_mode(self, value: set[AAPAProcessingOptions.INPUTOPTIONS])->set[AAPAProcessingOptions.INPUTOPTIONS]:
        if not value:
            return value
        match self.processing_mode:
            case AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN:
                value.discard(AAPAProcessingOptions.INPUTOPTIONS.EXCEL)
                value.discard(AAPAProcessingOptions.INPUTOPTIONS.SCAN)
        return value
    def _get_input_options(self)->set[AAPAProcessingOptions.INPUTOPTIONS]:
        processing_options: AAPAProcessingOptions = get_options_from_commandline(ArgumentOption.PROCES)
        return self._match_options_to_processing_mode(processing_options.input_options)
    @params.setter
    def params(self, value: AAPATuiParams):
        self.query_one(id2selector('root'), LabeledInput).input.value = value.root_directory
        self.query_one(id2selector('bbinput'), LabeledInput).input.value = value.bbinput_directory
        self.query_one(id2selector('output'), LabeledInput).input.value = value.output_directory
        self.query_one(id2selector('database'), LabeledInput).input.value = value.database
        self.query_one(id2selector('input'), LabeledInput).input.value = value.excel_in
    def _enable_input(self, id: str, value: bool):
        input_widget = self.query_one(id2selector(id), LabeledInput)
        input_widget.disabled = not value
        input_widget.visible = value                
    def enable_all(self):
        output_tab = self.query_one(id2selector('output_tab'))
        match self._processing_mode:
            case AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN:
                self._enable_input('input', True)
                self._enable_input('scanroot', True)
                self._enable_input('bbinput', False)
                output_tab.disabled = False

            case AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN:
                self._enable_input('input', False)
                self._enable_input('scanroot', False)
                self._enable_input('bbinput', True)
                output_tab.disabled = True
        
    @property 
    def processing_mode(self)->AAPAProcessingOptions.PROCESSINGMODE:
        return self._processing_mode
    @processing_mode.setter
    def processing_mode(self, value: AAPAProcessingOptions.PROCESSINGMODE|set[AAPAProcessingOptions.PROCESSINGMODE]):
        if isinstance(value,set):
            value = AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in value else AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN
        self._processing_mode = value
        self.enable_all()