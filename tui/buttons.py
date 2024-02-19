from textual.app import ComposeResult
from textual.widgets import Static, Button, RadioSet, RadioButton
from textual.containers import Horizontal
from data.classes.undo_logs import UndoLog
from main.log import log_debug

from tui.general.button_bar import ButtonBar, ButtonDef
from tui.general.utils import id2selector
from tui.common import BASE_CSS, MISSINGHELP, ToolTips

class AapaButtonsPanel(Static):
    DEFAULT_CSS = BASE_CSS + """
        AapaButtonsPanel {
            align: center middle;
            max-height: 5;
            background: $background;
            max-width: 150;   
            min-width: 120;
        }        
        AapaButtonsPanel ButtonBar {
            width: 56;
            max-width: 60;
            margin: 1 1 0 2;
        }
        AapaButtonsPanel Button {
            max-width: 12;
            outline: solid blue;
            margin: 0 1 0 1;
        }
        AapaButtonsPanel Button.not_next {
            outline: solid blue;
            background: $primary;
            color: $text;
            border-top: tall $primary-lighten-3;
            border-bottom: tall $primary-darken-3;
        }
        AapaButtonsPanel Button.not_next :hover {
            border-top: tall $panel;
            background: $panel-darken-2;
            color: $text;
        }
        AapaButtonsPanel Button.next {
            outline: double white;
            background: $primary;
            color: $text;
            border-top: tall $primary-lighten-3;
            border-bottom: tall $primary-darken-3;
        }
        AapaButtonsPanel Button.next :hover {
            border-top: tall $panel;
            background: $panel-darken-2;
            color: $text;
        }
        AapaButtonsPanel Label {
            margin: 1 0 0 2;
            color: black; 
        }
        AapaButtonsPanel .label {
            margin: 0;
            padding: 1;
        }
        .input--cursor {
            color: slategray;
        }
        .report_button {
            margin: 1 0 0 8;
        }
        .report_button :hover {
            border-top: tall $panel;
            background: $panel-darken-2;
            color: $text;
        }
    """
    def compose(self)->ComposeResult:
        with Horizontal():
            yield ButtonBar([ButtonDef('Input', variant= 'primary', id='scan', classes = 'not_next'),
                            ButtonDef('Form', variant= 'primary', id='form', classes = 'not_next'),
                            ButtonDef('Mail', variant= 'primary', id='mail', classes = 'not_next'), 
                            ButtonDef('Undo', variant= 'error', id='undo')], id='main'
                            )                 
            # yield(PreviewPanel())
            yield Button( 'Rapport', variant= 'default', id='report', classes = 'report_button') 
    def on_mount(self):
        log_debug ('mounting')
        tooltips = ToolTips.get('buttons', {})
        button_bar = self.query_one(id2selector('main'), ButtonBar)
        button_bar.styles.width = 6 + button_bar.nr_buttons() * 12
        for id in {'scan', 'form', 'mail', 'undo', 'report'}:
            self.query_one(id2selector(id), Button).tooltip = tooltips.get(id, MISSINGHELP)
        log_debug ('endmounting')
    def button(self, id: str)->Button:
        return self.query_one(id2selector(id), Button)
    def enable_action_buttons(self, undo_log: UndoLog):
        button_ids = {UndoLog.Action.INPUT: {'button': 'scan', 'next': 'form'},
                      UndoLog.Action.FORM: {'button': 'form', 'next': 'mail'}, 
                      UndoLog.Action.MAIL: {'button': 'mail', 'next': 'scan'}
                     } 
        next_button_id = button_ids[undo_log.action]['next'] if undo_log else 'scan'
        for button_id in {'scan', 'form', 'mail'} - {next_button_id}:
            self.button(button_id).classes = 'not_next'
        self.button(next_button_id).classes = 'next'
        self.button(next_button_id).focus()
        self.button('undo').disabled = not undo_log