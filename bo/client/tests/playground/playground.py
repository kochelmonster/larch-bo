from larch.bo.client.control import ControlContext
from larch.reactive import Reactive, rule, Cell

# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.server import run
from pathlib import Path

Date = Intl = window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass
def __new__(p): pass


if __name__ == "__main__":
    config_logging("hello.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": True,
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")


class Mixin:
    def plugin(self, call_order):
        call_order.append("Mixin")
        super().plugin(call_order)

class Base:
    def __init__(self, call_order):
        call_order.append("Base")

    def plugin(self, call_order):
        call_order.append("Base")

class Child(Mixin, Base):
    pass

class GrandChild(Child):
    pass


call_order = []
mixed = GrandChild(call_order)
console.log("call_order1", call_order)

call_order = []
mixed.plugin(call_order)
console.log("call_order1", call_order)
