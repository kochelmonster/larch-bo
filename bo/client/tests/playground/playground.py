# import larch.lib.adapter as adapter
from larch.bo.client.browser import start_main
from larch.bo.client.textlayout import LayoutBuilder

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


class Translation:
    def __init__(self, val):
        self.val = val

    def __str__(self):
        return "translated:" + self.val


def main():
    t = Translation("test")
    console.log(str(t))


start_main(main)
