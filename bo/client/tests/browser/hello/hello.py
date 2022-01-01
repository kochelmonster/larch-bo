# import larch.lib.adapter as adapter
from larch.bo.client.vaadin.vinput import register as input_register
from larch.bo.client.grid import Grid
from larch.bo.client.session import Session
from larch.bo.client.browser import start_main
from larch.reactive import Cell, rule

# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
# from larch.bo.server import run
from larch.bo.qt import run
from pathlib import Path

window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass


if __name__ == "__main__":
    config_logging("hello.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": True,
        "favicons": [dir_/"favicon.ico", dir_/"favicon-32x32.png"]
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")

input_register()


class Frame(Grid):
    layout = """
[.content]{cm}|<1>
  <1>
"""

    def __init__(self, context=None):
        super().__init__(context)
        self.content = Hello()


class Hello(Grid):
    layout = """
[.msg]{c}@text
[.name_]
[.greeting]
"""

    msg = Cell("")
    name_ = Cell("Jon")
    greeting = Cell("Hello")

    def modify_controls(self):
        self.control("name_").live().element.label = "Name"
        self.control("greeting").live().element.label = "Greeting"

    @rule
    def _rule_make_msg(self):
        self.msg = f"{self.greeting} {self.name_}"


def main():
    frame = Frame()
    frame.context["session"] = Session()  # __: opov
    window.session.set_root(frame)
    window.grid = frame.content


start_main(main)
