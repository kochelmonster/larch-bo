from time import time
from larch.reactive import Reactive, rule, Cell
from larch.bo.client.wc.vaadin import vbutton, vdialog, vprogress, styles
from larch.bo.client.grid import Grid
from larch.bo.client.i18n import gettext as _
from larch.bo.client.command import label
from larch.bo.client.control import ControlContext, register
from larch.bo.client.session import Session
from larch.bo.client.browser import start_main
from larch.bo.client.file import FileUploader, gui, FileItem


# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.api.file import FileUploader as APIFileUploader
from larch.bo.qt.start import run
from pathlib import Path

gui
styles
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
        "verbosity": 2,
        "transmitter": "socket",
        "window": {
            "frameless": False,
            # "width": 500,
            # "background": "#123456",
        }
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")

vbutton.register()
vprogress.register()


FILES = [
    {'mime': None, 'modified': 1641076453574.0,
     'name': 'index.html', 'path': None, 'size': 297},
    {'mime': None, 'modified': 1641076453574.0,
     'name': 'playground.js', 'path': None, 'size': 691036},
    {'mime': None, 'modified': 1640922092959.0,
     'name': 'index.html1', 'path': None, 'size': 313},
    {'mime': None, 'modified': 1640647984134.0,
     'name': 'out-main.log', 'path': None, 'size': 50099}]

FILES.extend(FILES)


class SimulatedUploader(Reactive):
    active_count = Cell()

    def __init__(self):
        self.files = [FileItem(f, self) for f in FILES]
        self.files[1].start = time()-1
        self.files[1].sent_bytes = 30000
        self.files[3].status = "aborted"
        self.files[3].error = "Aborted"

        self.files[4].sent_bytes = self.files[4].size
        self.files[4].status = "completed"
        self.active_count = len(self.files) - 2

    def update_active_count(self):
        self.active_count = len([f for f in self.files if f.status == "active"])

    def abort(self):
        self.files = []
        self.active_count = 0

    def __repr__(self):
        return f"<SimulatedUploader {self.active_count}>"


register(SimulatedUploader)(gui.FileUploaderControl)


@register(SimulatedUploader, "dialog")
@register(FileUploader, "dialog")
class UploadDialog(Grid):
    layout = """
[.context.value]@content
[.abort_all]{c}
<1>
"""
    element = Cell()

    @label(_("Abort All"))
    def abort_all(self):
        self.context.get("dialog").close()
        self.context.value.abort()

    @rule
    def _rule_change_label(self):
        if self.element and not self.context.value.active_count:
            if self.context.get("dialog").element.opened:
                self.contexts["abort_all"].set("label", "Close").control.update()


class Actions(Grid):
    layout = """
(1px,0)                                                                     |<1>
[.msg]{c}@html
(1px,0)|[.open_window]|[.upload_files]|[.select_directory]|[.dialog]|(1px,0)|
(1px,0)                                                                     |<1>
<1>    |                                                            |<1>
"""

    msg = "<h1>Choose an Action</h1>"

    def prepare_contexts(self):
        console.log("prepare context")
        self.contexts["dialog"].set("prefix", "error")

    def open_window(self):
        window.open(location.href, "_blank", "width=200,height=400,modal=yes")
        console.log("open window")

    def upload_files(self):
        def got_files(files):
            console.log("files", files)

        window.qt.choose_files("multi", "window.py", "").then(got_files)

        #uploader = FileUploader()
        #uploader.mode = "multi"
        #uploader.open_dialog().then(self.show_upload)

    def dialog(self):
        console.log("simulate layout")
        dialog = vdialog.Dialog(SimulatedUploader(), self.context, style="dialog")
        dialog.modal(self.upload_cancel, style="width: 80%")

    def select_directory(self):
        pass

    def show_upload(self, uploader):
        console.log("show uploader")
        dialog = vdialog.Dialog(uploader, self.context, style="dialog")
        dialog.modal(self.upload_cancel, noCloseOnOutsideClick=True, noCloseOnEsc=True,
                     style="width: 80%")

    def upload_cancel(self, dialog):
        console.log("upload cancel")


def main():
    frame = Actions()
    Session(frame).boot()
    window.grid = frame


start_main(main)
