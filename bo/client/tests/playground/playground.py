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

# __pragma__ ("jsiter")
obj = {"a": 1, "b": 2, "c": {"a": 1}}
a = []

for k in obj:
    # __pragma__ ("nojsiter")
    console.log("item", k, obj[k], type(obj[k]).__name__, type(obj[k]) == object)
