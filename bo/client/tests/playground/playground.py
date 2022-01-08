# import larch.lib.adapter as adapter
from larch.bo.client.browser import start_main
from larch.bo.client.textlayout import LayoutBuilder
from larch.bo.client.command import label

# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.server import run
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
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")



class ListHandler:
    def __init__(self):
        console.log("__init__ ListHandler")
        super().__init__()


class Control:
    def __init__(self):
        console.log("__init__ Control")
        super().__init__()


class Table(Control):
    def __init__(self):
        console.log("__init__ Table")
        super().__init__()


class FileView(ListHandler, Table):
    def ___init__(self):
        console.log("__init__ FileView")
        super().__init__()


f = FileView()


class API:
    def __getattr__(self, name):
        return None


api = API()
