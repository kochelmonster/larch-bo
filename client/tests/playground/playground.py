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


class Test:
    data = [1, 2, 3]


class TestChild(Test):
    pass


class TestChild2(Test):
    pass


t1 = TestChild()
console.log("t1.1", t1.data, [1, 2, 3])

t1.__class__.data = [4, 5, 6]
console.log("t1.2", t1.data, [4, 5, 6])

t2 = TestChild2()
console.log("t2.1", t2.data, [1, 2, 3])

t3 = TestChild()
console.log("t3.1", t3.data, [4, 5, 6])

t1.data = [7, 8, 9]
console.log("t1.3", t1.data, [7, 8, 9])
console.log("t2.2", t2.data, [1, 2, 3])
console.log("t3.2", t3.data, [4, 5, 6])
