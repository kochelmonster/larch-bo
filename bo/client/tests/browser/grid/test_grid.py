# import larch.lib.adapter as adapter
from larch.bo.client.vaadin.vinput import register as input_register
from larch.bo.client.vaadin.vbutton import register as button_register
from larch.bo.client.grid import Grid
from larch.bo.client.session import Session
from larch.bo.client.browser import BODY, start_main
from larch.bo.client.qt import create_window_container, calc_minsize
from larch.reactive import Cell, rule

# __pragma__("skip")
# ---------------------------------------------------
import os
import sys
from gevent import sleep
from logging import getLogger
from larch.lib.test import config_logging
# from larch.bo.server import run
from larch.bo.qt import run
from pathlib import Path

window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass


class GridApi:
    def get_data(self, count):
        for i in range(10):
            yield [{"name": "test"}] * count
            sleep(1)


if __name__ == "__main__":
    config_logging(os.environ.get("LARCH_BO_QT_FRONTEND_STARTED", "qt")+"-grid.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": True,
        "api": GridApi(),
        "transmitter": "socket",
        "window": {
            "frameless": False,
            "debugger": False,
            "width": 0,
            "height": 0,
        }
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")

require("./grid.scss")
input_register()
button_register()


class Frame(Grid):
    layout = """
(1px,1px)                          |<1>
(1px,1px)|[.content]|(1px,1px)
bottom:this is some button test{cb}|<1>
  <1>    |          | <1>
"""

    def __init__(self, context=None):
        super().__init__(context)
        self.content = TestGrid()


class TestGrid(Grid):
    layout = """
lvalue:Value{r}|[.value]{l}
               |[.to_text]
               |[.to_number]
               |[.to_form]
               |[.from_server]
               |[.abort]
               |[.calc_minsize]
[.output]@text
    <1>        |<1>
"""

    value = Cell("Test 123")
    output = Cell("")

    def prepare_contexts(self):
        self.contexts["value"]["no_label_float"] = True   # __: opov

    def modify_controls(self):
        self.show("abort", False)
        self.celement("output").classList.add("output")
        self.element.classList.add("TestGrid")

    def to_text(self):
        self.value = "test"
        console.log("submit")

    def to_number(self):
        self.value = 1.2
        console.log("submit")

    def to_form(self):
        self.value = SubGrid()

    def from_server(self):
        def receive(item):
            print("received item", item)
            self.output += repr(item) + "\n"

        def result(data):
            print("data", data)
            self.show("from_server")
            self.show("abort", False)

        def error(data):
            print("error", data)
            self.show("from_server")
            self.show("abort", False)

        self.show("from_server", False)
        self.show("abort")
        session = self.context["session"]  # __: opov
        self.request = session.extern.get_data(10).receive(receive).then(result, error)

    def abort(self):
        self.request.abort()
        self.show("from_server")
        self.show("abort", False)

    def calc_minsize(self):
        size = calc_minsize()
        self.output += f"min_size = {size}\n"

    def show(self, name, visible=True):
        self.contexts[name].element.style.display = "" if visible else "none"

    @rule
    def _rule_value_changed(self):
        print("output changed", repr(self.output), isinstance(self.output, str))


class SubGrid(Grid):
    layout = """
[.submit]|[.cancel]
"""

    def submit(self):
        pass

    def cancel(self):
        pass


def tabs_changed(event):
    print("tabs changed", event)


def adjust_size():
    size = calc_minsize()
    window.qt.set_size(*size)
    window.qt.set_minsize(*size)
    # window.qt.set_fixedsize(*size)


def main():
    print("start main")
    root_container = create_window_container(BODY)

    frame = Frame()
    print("--build frame")
    frame.context["session"] = Session(root_container)  # __: opov
    print("--set session")
    window.session.set_root(frame)
    window.grid = frame.content
    BODY.addEventListener("tabindex-done", tabs_changed)
    window.addEventListener("qtready", adjust_size)
    console.log("main ready")


def show_ready():
    print("qt-ready")


window.addEventListener("qtready", show_ready)

start_main(main)
# document.addEventListener('DOMContentLoaded', main)
