import ui

# __pragma__("skip")
# ---------------------------------------------------
import os
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.server import run

ui
logger = getLogger("main")


if __name__ == "__main__":
    config_logging(os.environ.get("LARCH_BO_QT_FRONTEND_STARTED", "qt")+"-grid.log", __file__)
    config = {"debug": True}
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")
