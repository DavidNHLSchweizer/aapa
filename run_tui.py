import logging
from tui.aapa_app import AAPAApp

if __name__ == "__main__":
    # logging.basicConfig(filename='terminal.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    app = AAPAApp()
    app.run()