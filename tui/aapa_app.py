from dataclasses import dataclass
import random
import logging
from textual.screen import Screen
from textual.widget import Widget
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Header, Footer, Static, Button, RadioSet, RadioButton
from textual.containers import Horizontal, Vertical
from aapa import AAPARunner
from data.classes.action_log import ActionLog
from general.args import AAPAConfigOptions, AAPAaction, AAPAOptions
from general.log import pop_console, push_console
from general.versie import BannerPart, banner
from process.aapa_processor.aapa_config import AAPAConfiguration
from tui.common.button_bar import ButtonBar, ButtonDef
from general.config import config
from tui.common.labeled_input import LabeledInput
from tui.common.required import Required
from tui.common.terminal import  TerminalScreen
from tui.common.verify import DialogMessage, verify
from tui.terminal_console import init_console, show_console
import tkinter.filedialog as tkifd

from tui.terminal_console import TerminalConsoleFactory

def AAPArun_script(options: AAPAOptions)->bool:
    try:
        push_console(TerminalConsoleFactory().create())
        aapa_runner = AAPARunner(options.config_options)
        aapa_runner.process(options.processing_options) 
    finally:
        pop_console()
    return True

ToolTips = {'root': 'De directory waarbinnen gezocht wordt naar (nieuwe) aanvragen',
            'output': 'De directory waar beoordelingsformulieren worden aangemaakt',
            'database':'De database voor het programma',
            'root-input-button': 'Kies de root-directory',
            'output-input-button': 'Kies de output-directory',
            'database-input-button': 'Kies de database',
            'scan': 'Zoek nieuwe aanvragen in root-directory/subdirectories',
            'form': 'Maak aanvraagformulieren',
            'mail': 'Zet mails klaar voor beoordeelde aanvragen',
            'undo': 'Maak de laatste actie (scan,form of mail) ongedaan',
            'mode_preview': 'Laat verloop van de acties zien; Geen wijzigingen in bestanden of database',
            'mode_uitvoeren': 'Voer acties uit. Wijzigingen in bestanden en database, kan niet worden teruggedraaid',
            'report': 'Schrijf alle aanvragen in de detabase naar een Excel-bestand',
            }
@dataclass
class AAPATuiParams:
    root_directory: str = ''
    output_directory: str = ''
    database: str = ''
    preview: bool = True
    def get_options(self, action: AAPAaction)->AAPAOptions:
        return AAPAOptions(actions=[action], root_directory=self.root_directory, 
                           output_directory=self.output_directory, database_file=self.database, preview=self.preview)
      
class AapaDirectoriesForm(Static):
    def compose(self)->ComposeResult:
        with Vertical():
            yield LabeledInput('Root directory', id='root', validators=Required(), button=True)
            yield LabeledInput('Output directory', id='output', validators=Required(), button=True)
            yield LabeledInput('Database', id='database', validators=Required(), button=True)
    def on_mount(self):
        self.border_title = 'AAPA Configuratie'
        for id in ['root', 'output', 'database']:
            self.query_one(f'#{id}', LabeledInput).input.tooltip = ToolTips[id]
        for id in ['root-input-button', 'output-input-button', 'database-input-button']:
            self.query_one(f'#{id}', Button).tooltip = ToolTips[id]
        self._load_config()
    def _load_config(self):        
        for id in {'root', 'output', 'database'}:
            self.query_one(f'#{id}', LabeledInput).value = config.get('configuration', id)
    def _store_config_id(self, id: str):
        for id in {'root', 'output', 'database'}:
            config.set('configuration', id, self.query_one(f'#{id}', LabeledInput).value)
    def _store_config(self):
        for id in {'root', 'output', 'database'}:
            self._store_config_id(id)
    def _select_directory(self, input_id: str, title: str):
        input = self.query_one(f'#{input_id}', LabeledInput).input
        if (result := tkifd.askdirectory(mustexist=True, title=title, initialdir=input.value)):
            input.value=result
            input.cursor_position = len(result)
            input.focus()
            self._store_config_id(input_id)
    def _select_file(self, input_id: str, title: str, default_file: str, default_extension: str):
        input = self.query_one(f'#{input_id}', LabeledInput).input
        if (result := tkifd.asksaveasfilename(initialfile=input.value, title=title, confirmoverwrite = False,
                                            filetypes=[(default_file, f'*{default_extension}'),('all files', '*')], defaultextension=default_extension)):
            input.value=result
            input.cursor_position = len(result)
            input.focus()
            self._store_config_id(input_id)
    def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case 'root-input-button': self.edit_root()
            case 'output-input-button': self.edit_output_directory()
            case 'database-input-button': self.edit_database()
        message.stop()
    def edit_root(self):
        self._select_directory('root', 'Selecteer root directory voor aanvragen)')
    def edit_output_directory(self):
        self._select_directory('output', 'Selecteer de output directory voor nieuwe formulieren')
    def edit_database(self):
        self._select_file('database','Select databasefile', 'database files', '.db')
    @property
    def params(self)-> AAPATuiParams:
        return AAPATuiParams(root_directory= self.query_one('#root', LabeledInput).input.value, 
                             output_directory= self.query_one('#output', LabeledInput).input.value,
                             database=self.query_one('#database', LabeledInput).input.value)
    @params.setter
    def params(self, value: AAPATuiParams):
        self.query_one('#root', LabeledInput).input.value = value.root_directory
        self.query_one('#output', LabeledInput).input.value = value.output_directory
        self.query_one('#database', LabeledInput).input.value = value.database
        
class AapaButtons(Static):
    def compose(self)->ComposeResult:
        with Horizontal():
            yield ButtonBar([ButtonDef('Scan', variant= 'primary', id='scan', classes = 'not_next'),
                             ButtonDef('Form', variant= 'primary', id='form', classes = 'not_next'),
                             ButtonDef('Mail', variant= 'primary', id='mail', classes = 'not_next'), 
                             ButtonDef('Undo', variant= 'error', id='undo')], 
                             ) 
            with RadioSet():
                yield RadioButton('preview', id='preview', value=True)
                yield RadioButton('uitvoeren', id='uitvoeren')
            yield Button('Rapport', variant = 'primary', id='report')
    def on_mount(self):
        button_bar = self.query_one(ButtonBar)
        button_bar.styles.width = 6 + button_bar.nr_buttons() * 12
        for id in {'scan', 'form', 'mail', 'undo', 'report'}:
            self.query_one(f'#{id}', Button).tooltip = ToolTips[id]
        for id in {'preview', 'uitvoeren'}:
            self.query_one(f'#{id}').tooltip = ToolTips[f'mode_{id}'] 
    def button(self, id: str)->Button:
        return self.query_one(f'#{id}', Button)
    def enable_action_buttons(self, action_log: ActionLog):
        button_ids = {ActionLog.Action.SCAN: {'button': 'scan', 'next': 'form'},
                      ActionLog.Action.FORM: {'button': 'form', 'next': 'mail'}, 
                      ActionLog.Action.MAIL: {'button': 'mail', 'next': 'scan'}
                     } 
        next_button_id = button_ids[action_log.action]['next'] if action_log else 'scan'
        for button_id in {'scan', 'form', 'mail'} - {next_button_id}:
            self.button(button_id).classes = 'not_next'
        self.button(next_button_id).classes = 'next'
        self.button(next_button_id).focus()
        self.button('undo').disabled = not action_log
    def toggle(self):
        self.preview = not self.preview
    @property
    def preview(self)->bool:
        return self.query_one('#preview', RadioButton).value
    @preview.setter
    def preview(self, value: bool):
        if value: #note: this is the only way it works properly
            self.query_one('#preview', RadioButton).value = True
        else:
            self.query_one('#uitvoeren', RadioButton).value= True
  
class EnableButtons(Message): pass

class AAPAApp(App):
    BINDINGS = [ 
                Binding('ctrl-c', 'einde', 'Einde', priority=True),
                Binding('ctrl+s', 'scan', 'Scan', priority = True),
                Binding('ctrl+f', 'form', 'Form', priority = True),
                Binding('ctrl+o', 'mail', 'Mail', priority = True),     # ctrl+m does not work while in Input fields, probably interferes with Enter    
                Binding('ctrl+z', 'undo', 'Undo', priority = True),
                Binding('ctrl+p', 'toggle_preview', 'Toggle preview', priority=True),
                Binding('ctrl+r', 'edit_root', 'Bewerk root directory', priority = True, show=False),
                Binding('ctrl+o', 'edit_output_directory', 'Bewerk output directory', priority = True, show=False),
                Binding('ctrl+b', 'edit_database', 'Kies database file', priority = True, show=False),
                Binding('ctrl+q', 'barbie', '', priority = True, show=False),
               ]
    CSS_PATH = ['aapa.tcss']
    def __init__(self, **kwdargs):
        self.terminal_active = False
        self.last_action: ActionLog = None
        self.barbie = False
        self.barbie_oldcolors = {}
        super().__init__(**kwdargs)
    def compose(self) -> ComposeResult:
        yield Header()
        yield AapaDirectoriesForm()
        yield AapaButtons()
        yield Footer()
    @property
    def terminal(self)->TerminalScreen:
        if not hasattr(self, '_terminal'):
            self._terminal = self.get_screen('terminal')
            global global_terminal 
            global_terminal = self._terminal
        return self._terminal
    def callback(self, result: bool):
        self.post_message(EnableButtons())
    async def on_enable_buttons(self, message: EnableButtons):
        await self.enable_buttons()
    async def on_mount(self):
        self.title = banner(BannerPart.BANNER_TITLE)
        self.sub_title = banner(BannerPart.BANNER_VERSION)
        await init_console(self, self.callback)
        self.post_message(EnableButtons())
    async def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case 'scan': await self.action_scan()
            case 'form': await self.action_form()
            case 'mail': await self.action_mail()
            case 'undo': await self.action_undo()
            case 'report': await self.action_report()
        message.stop()
    def _create_options(self, **kwdargs)->AAPAOptions:
        options = self.params.get_options(kwdargs.pop('action', None))
        options.processing_options.filename = kwdargs.pop('filename', options.processing_options.filename)
        return options
    async def run_AAPA(self, action: AAPAaction, **kwdargs):
        options = self._create_options(action=action, **kwdargs)
        # logging.info(f'{options}')
        if await show_console():
            self.terminal.run(AAPArun_script,options=options)             
    async def action_scan(self):    
        await self.run_AAPA(AAPAaction.SCAN)
    async def action_form(self):    
        await self.run_AAPA(AAPAaction.FORM)
    async def action_mail(self):
        await self.run_AAPA(AAPAaction.MAIL)
    def refresh_last_action(self)->ActionLog:
        options = self._create_options()
        configuration = AAPAConfiguration(options.config_options)
        if not configuration.initialize(options.processing_options, AAPAConfiguration.PART.DATABASE):
            result = None
        else:
            result = configuration.storage.action_logs.last_action()
        self.last_action = result 
        return result
    async def enable_buttons(self):
        self.refresh_last_action()
        self.query_one(AapaButtons).enable_action_buttons(self.last_action)
    async def action_undo(self):
        if self.query_one(AapaButtons).preview:
            await self.run_AAPA(AAPAaction.UNDO)
        else:
            verify(self, f'Laatste actie (wordt teruggedraaid):\n{self.last_action.summary()}\n\nWAARSCHUWING:\nAls je voor "Ja" kiest kunnen bestanden worden verwijderd en wordt de database aangepast.\nDit kan niet meer ongedaan worden gemaakt.\n\nWeet je zeker dat je dit wilt?', 
                   originator_key='verify_undo')              
    async def on_dialog_message(self, event: DialogMessage):
        match event.originator_key:
            case 'verify_undo':                              
                if str(event.result_str) == 'Ja': 
                    await self.run_AAPA(AAPAaction.UNDO)
    async def action_report(self):
        if (filename := tkifd.asksaveasfilename(title='Bestandsnaam voor rapportage', defaultextension='.xslx', 
                                           filetypes=[('*.xlsx', 'Excel bestanden'), ('*.*', 'Alle bestanden')],
                                           initialfile=config.get('report', 'filename'),
                                           confirmoverwrite=True)):
            await self.run_AAPA(AAPAaction.REPORT,filename=filename)
    @property 
    def directories_form(self)->AapaDirectoriesForm:
        return self.query_one(AapaDirectoriesForm)
    @property 
    def params(self)->AAPATuiParams:
        result = self.directories_form.params
        result.preview = self.query_one(AapaButtons).preview
        return result
    @params.setter
    def params(self, value: AAPATuiParams):
        self.directories_form.params = value
        self.query_one(AapaButtons).preview = value.preview
    def __get_config_options(self)->AAPAConfigOptions:
        return AAPAConfigOptions(root_directory=self.params.root_directory,
                                 output_directory=self.params.output_directory, 
                                 database_file=self.params.database)                                 
    def action_toggle_preview(self):
        self.query_one(AapaButtons).toggle()
    def action_edit_root(self):
        self.directories_form.edit_root()
    def action_edit_forms(self):
        self.directories_form.edit_output_directory()
    def action_edit_database(self):
        self.directories_form.edit_database()
    def action_einde(self):
        self.exit()
    def _animate_widget_attribute(self, widget: Widget, attribute, target, duration):
        result = getattr(widget.styles, attribute, None)
        widget.styles.animate(attribute, target, duration = duration*(1+ random.random()))
        return result
    def action_barbie(self):
        BARBIE = '#e0218a'
        self.barbie = not self.barbie
        for widget in self.query():
            if not isinstance(widget, Screen):
                oldbackground = self._animate_widget_attribute(widget, 'background', BARBIE if self.barbie else self.barbie_oldcolors[widget]['background'], 3.0)
                oldcolor = self._animate_widget_attribute(widget, 'color', 'white' if self.barbie else self.barbie_oldcolors[widget]['color'], 4.0)
                self.barbie_oldcolors[widget] = {'background': oldbackground, 'color': oldcolor} 
                       
if __name__ == "__main__":
    logging.basicConfig(filename='test.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    app = AAPAApp()
    app.run()