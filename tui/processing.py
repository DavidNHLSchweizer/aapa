from textual.app import ComposeResult
from textual.widgets import Static, RadioSet, RadioButton
from textual.containers import Horizontal
from main.options import AAPAProcessingOptions
from tui.general.utils import id2selector
from tui.common import BASE_CSS, MISSINGHELP, ProcessingModeChanged, ToolTips

class RadioSetPanel(Static):
    def __init__(self, radioset_id: str, values: list[str], **kwdargs):
        self._values = values
        self._radioset_id = radioset_id
        super().__init__(**kwdargs)
    def compose(self)->ComposeResult:
        with RadioSet(id=self._radioset_id):
            for n,value in enumerate(self._values):
                yield RadioButton(value, id=value, value=n==0)

class PreviewPanel(RadioSetPanel):
    def __init__(self, **kwdargs):
        super().__init__(radioset_id='is_preview', values=['preview', 'uitvoeren'], **kwdargs)

class ModePanel(RadioSetPanel):
    def __init__(self, **kwdargs):
        super().__init__(radioset_id='mode', values=['aanvragen', 'verslagen'], **kwdargs)

class AapaProcessingForm(Static):
    DEFAULT_CSS = BASE_CSS + """
        AapaProcessingForm {
            height: 5;
            background: $background;
            margin: 0;
            border: round $border;
        }
        AapaProcessingForm RadioSetPanel {
            max-width: 38;
            min-width: 38;
            padding: 0 0 0 0;
        }
        AapaProcessingForm RadioSet {
            layout: horizontal;
            outline: solid $border;    
            margin: 0 2 0 2;
        }
        AapaProcessingForm RadioButton {
            color: black; 
        }
    """
    def compose(self)->ComposeResult:
        with Horizontal():
            yield(ModePanel())
            yield(PreviewPanel())
    def on_mount(self):
        self.border_title = 'Verwerking'
        tooltips = ToolTips.get('processing', {})
        for id in {'preview', 'uitvoeren', 'aanvragen', 'verslagen'}:
            self.query_one(id2selector(id)).tooltip = tooltips.get(f'mode_{id}', MISSINGHELP) 
    def toggle(self):
        self.preview = not self.preview
    @property
    def preview(self)->bool:
        return self.query_one(id2selector('preview'), RadioButton).value
    @preview.setter
    def preview(self, value: bool):
        if value: #note: this is the only way it works properly
            self.query_one(id2selector('preview'), RadioButton).value = True
        else:
            self.query_one(id2selector('uitvoeren'), RadioButton).value= True
    @property
    def processing_mode(self)->AAPAProcessingOptions.PROCESSINGMODE:       
        if self.query_one(id2selector('aanvragen'), RadioButton).value == True:
            return AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN
        elif self.query_one(id2selector('verslagen'), RadioButton).value == True:
            return AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN
    @processing_mode.setter
    def processing_mode(self, value: AAPAProcessingOptions.PROCESSINGMODE):
        match value:
            case AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN:
                self.query_one(id2selector('aanvragen'), RadioButton).value = True
            case AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN:
                self.query_one(id2selector('verslagen'), RadioButton).value = True
    def on_radio_set_changed(self, message:RadioSet.Changed):
        if message.radio_set.id == 'mode':
            self.app.post_message(ProcessingModeChanged(self.processing_mode))


