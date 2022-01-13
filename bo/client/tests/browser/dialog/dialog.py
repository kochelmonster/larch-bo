# import larch.lib.adapter as adapter
from larch.reactive import Cell, rule
from larch.bo.client.vaadin import vinput, vbutton, vdialog
from larch.bo.client.grid import Grid
from larch.bo.client.grid.snippets import OkCancel
from larch.bo.client.command import label
from larch.bo.client.control import ControlContext
from larch.bo.client.session import Session
from larch.bo.client.browser import start_main
# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.server import run
from pathlib import Path

location = window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass


if __name__ == "__main__":
    config_logging("hello.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": False,
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")

vbutton.register()
vinput.register()


clas


class Hello(Grid):
    layout = """
[.msg]{c}@text
[.name_]
[.greeting]
(0, 1em)         |<1>
[.buttons]{r}
<1>
"""

    msg = Cell("")
    name_ = Cell("Jon")
    greeting = Cell("Hello")
    result = False

    def __init__(self, *args):
        super().__init__(*args)
        self.buttons = OkCancel()

    def modify_controls(self):
        el = self.control("name_").live().element
        el.label = "Name"
        el.style.width = "100%"
        el = self.control("greeting").live().element
        el.label = "Greeting"
        el.style.width = "100%"

    def ok(self):
        print("ok", self.parent)
        self.result = True
        self.context.get("dialog").close()

    def cancel(self):
        print("cancel", self.parent)
        self.context.get("dialog").close()

    @rule
    def _rule_make_msg(self):
        self.msg = f"{self.greeting} {self.name_}"


class Actions(Grid):
    layout = """
(1px,0)               |<1>
[.msg]{c}@html
[.open_dialog]{c}
(1px,0)               |<1>
<1>
"""

    msg = "<h1>Choose an Action</h1>"

    @label("Open Dialog")
    def open_dialog(self):
        dialog = vdialog.Dialog(Hello(), self.context)
        dialog.modal(self.dialog_done, style="min-width: 40%", draggable=True, resizable=True)

    def dialog_done(self, dialog):
        print("dialog done", dialog.value.result)


def main():
    Session(Actions()).boot()


start_main(main)
