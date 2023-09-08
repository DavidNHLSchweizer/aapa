from dataclasses import dataclass
import random
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, RadioSet, RadioButton
from textual.containers import Horizontal, Vertical
from aapa import AAPA
from general.args import AAPAaction, AAPAoptions
from general.log import pop_console, push_console
from tui.common.button_bar import ButtonBar, ButtonDef
from general.config import config
from tui.common.labeled_input import LabeledInput
from tui.common.required import Required
from tui.common.terminal import TerminalScreen
from tui.terminal_console import init_console, show_console
import logging
import tkinter.filedialog as tkifd

from tui.terminal_console import TerminalConsoleFactory

def AAPArun_script(options: AAPAoptions)->bool:
    try:
        push_console(TerminalConsoleFactory().create())
        aapa_script = AAPA(options)
        aapa_script.process() 
    finally:
        pop_console()
    return True

ToolTips = {'root': 'De directory waarbinnen gezocht wordt naar (nieuwe) aanvragen',
            'forms': 'De directory waar beoordelingsformulieren worden aangemaakt',
            'database':'De database voor het programma',
            'root-input-button': 'Kies de directory',
            'forms-input-button': 'Kies de directory',
            'database-input-button': 'Kies de database',
            'scan': 'Zoek nieuwe aanvragen in root-directory/subdirectories, maak aanvraagformulieren',
            'mail': 'Zet mails klaar voor beoordeelde aanvragen',
            'mode_preview': 'Laat verloop van de acties zien; Geen wijzigingen in bestanden of database',
            'mode_uitvoeren': 'Voer acties uit. Wijzigingen in bestanden en database, kan niet worden teruggedraaid',
            'report': 'Schrijf alle aanvragen in de detabase naar een Excel-bestand',
            }
@dataclass
class AAPATuiParams:
    root_directory: str = ''
    forms_directory: str = ''
    database: str = ''
    preview: bool = True
    def get_options(self, action: AAPAaction)->AAPAoptions:
        return AAPAoptions([action], self.root_directory, self.forms_directory, self.database, self.preview)
      
class AapaConfiguration(Static):
    def compose(self)->ComposeResult:
        with Vertical():
            yield LabeledInput('Root directory', id='root', validators=Required(), button=True)
            yield LabeledInput('Forms directory', id='forms', validators=Required(), button=True)
            yield LabeledInput('Database', id='database', validators=Required(), button=True)
    def on_mount(self):
        self.border_title = 'AAPA Configuratie'
        for id in ['root', 'forms', 'database']:
            self.query_one(f'#{id}', LabeledInput).input.tooltip = ToolTips[id]
        for id in ['root-input-button', 'forms-input-button', 'database-input-button']:
            self.query_one(f'#{id}', Button).tooltip = ToolTips[id]
        self._load_config()
    def _load_config(self):        
        self.query_one('#root', LabeledInput).value = config.get('configuration', 'root')
        self.query_one('#forms', LabeledInput).value = config.get('configuration', 'forms')
        self.query_one('#database', LabeledInput).value = config.get('configuration', 'database')
    def _select_directory(self, input_id: str, title: str):
        input = self.query_one(f'#{input_id}', LabeledInput).input
        if (result := tkifd.askdirectory(mustexist=True, title=title, initialdir=input.value)):
            input.value=result
            input.cursor_position = len(result)
            input.focus()
    def _select_file(self, input_id: str, title: str, default_file: str, default_extension: str):
        input = self.query_one(f'#{input_id}', LabeledInput).input
        if (result := tkifd.asksaveasfilename(initialfile=input.value, title=title, confirmoverwrite = False,
                                            filetypes=[(default_file, f'*{default_extension}'),('all files', '*')], defaultextension=default_extension)):
            input.value=result
            input.cursor_position = len(result)
            input.focus()
    def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case 'root-input-button': self.edit_root()
            case 'forms-input-button': self.edit_forms()
            case 'database-input-button': self.edit_database()
        message.stop()
    def edit_root(self):
        self._select_directory('root', 'Select root directory')
    def edit_forms(self):
        self._select_directory('forms', 'Select forms directory')
    def edit_database(self):
        self._select_file('database','Select databasefile', 'database files', '.db')
    @property
    def params(self)-> AAPATuiParams:
        return AAPATuiParams(root_directory= self.query_one('#root', LabeledInput).input.value, 
                             forms_directory= self.query_one('#forms', LabeledInput).input.value,
                             database=self.query_one('#database', LabeledInput).input.value)
    @params.setter
    def params(self, value: AAPATuiParams):
        self.query_one('#root', LabeledInput).input.value = value.root_directory
        self.query_one('#forms', LabeledInput).input.value = value.forms_directory
        self.query_one('#database', LabeledInput).input.value = value.database
        
class AapaButtons(Static):
    def compose(self)->ComposeResult:
        with Horizontal():
            yield ButtonBar([ButtonDef('Scan', variant= 'primary', id='scan'),
                             ButtonDef('Mail', variant= 'primary', id='mail')]) 
            with RadioSet():
                yield RadioButton('preview', id='preview', value=True)
                yield RadioButton('uitvoeren', id='uitvoeren')
            yield Button('Rapport', variant = 'primary', id='report')
    def on_mount(self):
        self.query_one(ButtonBar).styles.width = 36
        for id in {'scan', 'mail', 'report'}:
            self.query_one(f'#{id}', Button).tooltip = ToolTips[id]
        for id in {'preview', 'uitvoeren'}:
            self.query_one(f'#{id}').tooltip = ToolTips[f'mode_{id}']    
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
  
class AAPAApp(App):
    BINDINGS = [ 
                Binding('ctrl-c', 'einde', 'Einde programma', priority=True),
                Binding('ctrl+s', 'scan', 'Scan nieuwe aanvragen', priority = True),
                Binding('ctrl+o', 'mail', 'Zet mails klaar', priority = True),     # ctrl+m does not work while in Input fields, probably interferes with Enter    
                Binding('ctrl+p', 'toggle_preview', 'Toggle preview mode', priority=True),
                Binding('ctrl+r', 'edit_root', 'Bewerk root directory', priority = True, show=False),
                Binding('ctrl+f', 'edit_forms', 'Bewerk forms directory', priority = True, show=False),
                Binding('ctrl+d', 'edit_database', 'Kies database file', priority = True, show=False),
                Binding('ctrl+q', 'barbie', '', priority = True, show=False),
               ]
    CSS_PATH = ['aapa.tcss']
    def __init__(self, **kwdargs):
        self.terminal_active = False
        self.barbie = False
        self.barbie_oldcolors = {}
        super().__init__(**kwdargs)
    def compose(self) -> ComposeResult:
        yield Header()
        yield AapaConfiguration()
        yield AapaButtons()
        yield Footer()
    @property
    def terminal(self)->TerminalScreen:
        if not hasattr(self, '_terminal'):
            self._terminal = self.get_screen('terminal')
            global global_terminal 
            global_terminal = self._terminal
        return self._terminal
    async def on_mount(self):
        await init_console(self)
    async def on_button_pressed(self, message: Button.Pressed):
        # logging.debug(f'button {message.button.id}')
        match message.button.id:
            case 'scan': await self.action_scan()
            case 'mail': await self.action_mail()
            case 'report': await self.action_report()
        message.stop()
    def _create_options(self, **kwdargs)->AAPAoptions:
        options = self.params.get_options(kwdargs.pop('action', None))
        options.filename = kwdargs.pop('filename', options.filename)
        return options
    async def run_AAPA(self, action: AAPAaction, **kwdargs):
        options = self._create_options(action=action, **kwdargs)
        # logging.info(f'{options}')
        if await show_console():
            self.terminal.run(AAPArun_script,options=options)                
    
    async def action_scan(self):    
        await self.run_AAPA(AAPAaction.SCAN)
    async def action_mail(self):
        await self.run_AAPA(AAPAaction.MAIL)
    async def action_report(self):
        if (filename := tkifd.asksaveasfilename(title='Bestandsnaam voor rapportage', defaultextension='.xslx', 
                                           filetypes=[('*.xlsx', 'Excel bestanden'), ('*.*', 'Alle bestanden')],
                                           initialfile=config.get('report', 'filename'),
                                           confirmoverwrite=True)):
            await self.run_AAPA(AAPAaction.REPORT,filename=filename)
    
    @property 
    def params(self)->AAPATuiParams:
        result = self.query_one(AapaConfiguration).params
        result.preview = self.query_one(AapaButtons).preview
        return result
    @params.setter
    def params(self, value: AAPATuiParams):
        self.query_one(AapaConfiguration).params = value
        self.query_one(AapaButtons).preview = value.preview
    def action_toggle_preview(self):
        self.query_one(AapaButtons).toggle()
    def action_edit_root(self):
        self.query_one(AapaConfiguration).edit_root()
    def action_edit_forms(self):
        self.query_one(AapaConfiguration).edit_forms()
    def action_edit_database(self):
        self.query_one(AapaConfiguration).edit_database()
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