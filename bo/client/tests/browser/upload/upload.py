from larch.reactive import Reactive, Cell, Pointer, rule
from larch.bo.client.vaadin import vbutton, vdialog, vprogress
from larch.bo.client.grid import Grid
from larch.bo.client.i18n import gettext as _, label
from larch.bo.client.control import ControlContext, register
from larch.bo.client.session import Session
from larch.bo.client.browser import start_main, BODY
from larch.bo.client.file import FileUploader, gui, FileItem
from operator import itemgetter


# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.api.file import FileUploader as APIFileUploader
from larch.bo.server import run
from pathlib import Path

location = window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass
gui

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
            "width": 500,
            "background": "#123456",
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
        self.files[1].sent_bytes = 10000
        self.active_count = len(self.files)
        p = Pointer(self).files[0]  # __:opov
        r = p.__call__()
        console.log("p", repr(r), repr(self.files[0]), repr(itemgetter(0)(self.files)))

    def remove(self, id_):
        self.files = [f for f in self.files if f.id != id_]
        self.active_count = len(self.files)
        self.active_index = min(self.active_index, self.active_count-1)

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

    @label(_("Abort All"))
    def abort_all(self):
        console.log("Abort all")
        self.context.value.abort()

    @rule
    def _rule_close_when_finished(self):
        console.log("_rule_close_when_finished", self.context.value.active_count)
        if not self.context.value.active_count:
            self.context["dialog"].close()  # __:opov


class Actions(Grid):
    layout = """
(1px,0)                                                                     |<1>
[.msg]{c}@html
(1px,0)|[.open_window]|[.upload_files]|[.select_directory]|[.dialog]|(1px,0)|
(1px,0)                                                                     |<1>
<1>    |                                                            |<1>
"""

    msg = "<h1>Choose an Action</h1>"

    def open_window(self):
        window.open(location.href, "_blank", "width=200,height=400,modal=yes")
        console.log("open window")

    def upload_files(self):
        uploader = FileUploader()
        uploader.mode = "multi"
        uploader.open_dialog().then(self.show_upload)

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
    frame = Actions(ControlContext(session=Session(BODY)))
    window.session.set_root(frame)
    window.grid = frame.content


start_main(main)
