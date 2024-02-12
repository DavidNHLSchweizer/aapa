""" main Textual User Interface App. Run this from run_tui.py. """
import random
import logging
from textual.screen import Screen
from textual.widget import Widget
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Header, Footer, Button
from aapa import AAPARunner
from data.classes.undo_logs import UndoLog
from data.general.roots import Roots
from storage.queries.undo_logs import UndoLogQueries
from main.args import  AAPAProcessingOptions, AAPAaction, AAPAOptions, ArgumentOption, get_options_from_commandline
from main.log import log_debug, pop_console, push_console
from main.versie import BannerPart, banner
from process.main.aapa_config import AAPAConfiguration
from tui.buttons import AapaButtonsPanel
from tui.configuration import AapaConfigurationForm
from tui.processing import AapaProcessingForm
from main.config import config
from tui.general.terminal import  TerminalScreen
from tui.general.verify import DialogMessage, verify
from tui.common import BASE_CSS, AAPATuiParams, ProcessingModeChanged, windows_style
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
    DEFAULT_CSS = BASE_CSS
    def __init__(self, **kwdargs):
        self.terminal_active = False
        self.last_action: UndoLog = None
        self.barbie = False
        self.barbie_oldcolors = {}
        self._init_onedrive_root()
        super().__init__(**kwdargs)
    def compose(self) -> ComposeResult:
        yield Header()
        yield AapaConfigurationForm()
        yield AapaProcessingForm()
        yield AapaButtonsPanel()
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
    def _sync_app_with_commandline(self):
        processing_options:AAPAProcessingOptions = get_options_from_commandline(ArgumentOption.PROCES)
        if processing_options.processing_mode == {AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN}:
            self.processing_mode = AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN
        else:
            self.processing_mode = AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN        
        self.input_options = processing_options.input_options
    @property
    def input_options(self)->AAPAProcessingOptions.INPUTOPTIONS:
        return self.config_form.input_options
    @input_options.setter
    def input_options(self,value: AAPAProcessingOptions.INPUTOPTIONS):
        self.config_form.input_options= value
    @property
    def processing_mode(self)->AAPAProcessingOptions.PROCESSINGMODE:
        return self.process_form.processing_mode
    @processing_mode.setter
    def processing_mode(self,value: AAPAProcessingOptions.PROCESSINGMODE):
        self.process_form.processing_mode = value
    def _init_onedrive_root(self):
        processing_options:AAPAProcessingOptions = get_options_from_commandline(ArgumentOption.PROCES)
        if processing_options.onedrive:
            Roots.set_onedrive_root(processing_options.onedrive)       
    async def on_enable_buttons(self, message: EnableButtons):
        await self.enable_buttons()
    async def on_mount(self):
        self.title = banner(BannerPart.BANNER_TITLE)
        self.sub_title = banner(BannerPart.BANNER_VERSION)
        await init_console(self, self.callback)
        self._sync_app_with_commandline()
        self.post_message(EnableButtons())
    async def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case 'scan': await self.action_input()
            case 'form': await self.action_form()
            case 'mail': await self.action_mail()
            case 'undo': await self.action_undo()
            case 'report': await self.action_report()
        message.stop()
    def _create_options(self, **kwdargs)->AAPAOptions:
        return self.params.get_options(kwdargs.pop('action', None),  kwdargs.pop('filename', config.get('report', 'filename')))
    async def run_AAPA(self, action: AAPAaction, **kwdargs):
        options = self._create_options(action=action, **kwdargs)
        # logging.info(f'{options}')
        if await show_console():
            self.terminal.run(AAPArun_script,options=options)             
    async def action_input(self):    
        await self.run_AAPA(AAPAaction.INPUT)
    async def action_form(self):    
        await self.run_AAPA(AAPAaction.FORM)
    async def action_mail(self):
        await self.run_AAPA(AAPAaction.MAIL)
    def refresh_last_action(self)->UndoLog:
        log_debug('Refresh last')
        options = self._create_options()
        configuration = AAPAConfiguration(options.config_options)
        if configuration.initialize(options.processing_options, AAPAConfiguration.PART.DATABASE):
            queries : UndoLogQueries = configuration.storage.queries('undo_logs')
            self.last_action = queries.last_undo_log()
            log_debug(f'Refresh last {self.last_action}')
            return self.last_action
        log_debug('Refresh last none')
        return None
    async def enable_buttons(self):
        self.refresh_last_action()
        self.query_one(AapaButtonsPanel).enable_action_buttons(self.last_action)
    async def action_undo(self):
        if self.query_one(AapaProcessingForm).preview:
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
        if (filename := windows_style(tkifd.asksaveasfilename(title='Bestandsnaam voor rapportage', defaultextension='.xslx', 
                                           filetypes=[('*.xlsx', 'Excel bestanden'), ('*.*', 'Alle bestanden')],
                                           initialfile=config.get('report', 'filename'),
                                           confirmoverwrite=True))):
            await self.run_AAPA(AAPAaction.REPORT,filename=filename)
    @property 
    def config_form(self)->AapaConfigurationForm:
        return self.query_one(AapaConfigurationForm)
    @property 
    def process_form(self)->AapaProcessingForm:
        return self.query_one(AapaProcessingForm)
    @property 
    def params(self)->AAPATuiParams:
        result = self.config_form.params
        result.preview = self.query_one(AapaProcessingForm).preview
        result.input_options = self.query_one(AapaConfigurationForm).input_options
        result.processing_mode = self.query_one(AapaConfigurationForm).processing_mode
        return result
    @params.setter
    def params(self, value: AAPATuiParams):
        self.config_form.params = value
        self.process_form.preview = value.preview                       
        self.config_form.input_options = value.input_options
        self.config_form.processing_mode = value.processing_mode
    def action_toggle_preview(self):
        self.query_one(AapaProcessingForm).toggle()
    def action_edit_root(self):
        self.config_form.edit_root()
    def action_edit_forms(self):
        self.config_form.edit_output_directory()
    def action_edit_database(self):
        self.config_form.edit_database()
    def action_einde(self):
        self.exit()
    def _animate_widget_attribute(self, widget: Widget, attribute, target, duration):
        result = getattr(widget.styles, attribute, None)
        widget.styles.animate(attribute, target, duration = duration*(1+ random.random()))
        return result
    def on_processing_mode_changed(self, message: ProcessingModeChanged):
        self.config_form.processing_mode = message.mode      
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