# import larch.lib.adapter as adapter
from larch.bo.client.vaadin.vbutton import register as button_register
from larch.bo.client.vaadin.vdialog import Dialog
from larch.bo.client.grid import Grid
from larch.bo.client.control import ControlContext
from larch.bo.client.session import Session
from larch.bo.client.browser import start_main, BODY
from larch.bo.client.file import FileUploader


# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.api.file import FileUploader as APIFileUploader
# from larch.bo.server import run
from larch.bo.qt import run
from pathlib import Path

location = window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass


if __name__ == "__main__":
    config_logging("out.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "api": APIFileUploader(),
        "debug": True,
        "transmitter": "socket",
        "window": {
            "frameless": False,
            "width": 500,
            "background": "#123456",
        }
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")

button_register()


class Actions(Grid):
    layout = """
(1px,0)                                                           |<1>
[.msg]{c}@html                                                    |
(1px,0)|[.open_window]|[.upload_files]|[.select_directory]|(1px,0)|
(1px,0)                                                           |<1>
<1>    |                                                  |<1>
"""

    msg = "<h1>Choose an Action</h1>"

    def open_window(self):
        window.open(location.href, "_blank", "width=200,height=400,modal=yes")
        console.log("open window")

    def upload_files(self):
        uploader = FileUploader()
        uploader.mode = "multi"
        uploader.open_dialog().then(self.show_upload)

    def select_directory(self):
        pass

    def show_upload(self, uploader):
        dialog = Dialog(ControlContext(uploader, self.context))
        dialog.modal()


def main():
    frame = Actions(ControlContext(session=Session(BODY)))
    window.session.set_root(frame)
    window.grid = frame.content


start_main(main)
