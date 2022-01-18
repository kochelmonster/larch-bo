import ui

# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from faker import Factory
from larch.lib.test import config_logging
from larch.bo.server import run

ui
logger = getLogger("main")


fake = Factory.create()
fake.seed(4320)


DATA = [
    {
        "name": fake.name(),
        "office": fake.city(),
        "age": 18 + fake.pyint() % 60,
        "start": fake.date_time_this_decade().date()
    } for i in range(1000)
]


class API:
    def load_data(self, start, end):
        return DATA   # [start:end]


if __name__ == "__main__":
    config_logging("table.log", __file__)
    config = {
        "debug": True,
        "transmitter": "socket",
        "api": API()}
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")
