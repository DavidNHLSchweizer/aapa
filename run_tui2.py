from general.args import get_debug
from process.aapa_processor.aapa_config import LOGFILENAME
from general.log import init_logging

from tui.aapa_app2 import AAPAApp
if __name__ == "__main__":
    init_logging(LOGFILENAME, get_debug())
    app = AAPAApp()
    app.run()