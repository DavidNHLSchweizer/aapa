from main.args import get_debug
from process.main.aapa_config import LOGFILENAME
from main.log import init_logging

from tui.aapa_app import AAPAApp
if __name__ == "__main__":
    init_logging(LOGFILENAME, get_debug())
    app = AAPAApp()
    app.run()