from process.aapa_processor.aapa_config import LOGFILENAME
from general.log import init_logging

from tui.aapa_app import AAPAApp
if __name__ == "__main__":
    init_logging(LOGFILENAME)
    app = AAPAApp()
    app.run()