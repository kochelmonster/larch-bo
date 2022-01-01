# import larch.lib.adapter as adapter
from larch.bo.client.browser import start_main
from larch.reactive import Cell, rule, atomic, Reactive

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


# __pragma__("kwargs")
def kwargtest(a=1, b=2, c=3, **kwargs):
    return a, b, c, kwargs
# __pragma__("nokwargs")


def main():
    test = kwargtest(b="test", u=3)
    print("test", test)


start_main(main)
