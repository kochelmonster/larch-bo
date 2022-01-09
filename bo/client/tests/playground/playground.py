from larch.bo.client.control import ControlContext
from larch.reactive import Reactive, rule, Cell

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


class Table(Reactive):
    value = Cell()

    def __init__(self, context):
        self.context = context

    @rule
    def _rule_set(self):
        console.log("set context", self.value)
        self.context.set("test", self.value)

    @rule
    def _rule_observe(self):
        console.log("observe", self.context.observe("test"))


context = ControlContext()
table = Table(context)

context.set("test", 1)
context.set("test", 2)
window.context = context
window.table = table
