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


def main():
    b = LayoutBuilder()
    row1 = b.columns("[test]", "label", "<1>")
    row2 = b.columns("a", "b", "<1>")
    console.log(row1.join())
    console.log(row2.join())


start_main(main)
