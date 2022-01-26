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


def make_record(index):
    return {
        "id_": index,
        "name": fake.name(),
        "office": fake.city(),
        "age": 18 + fake.pyint() % 60,
        "salary": fake.pydecimal(min_value=450, max_value=10000, right_digits=2),
        "start": fake.date_time_this_decade().date(),
        "address": fake.address()
    }


DATA = [make_record(i) for i in range(1000)]


class API:
    def load_data(self, start, end):
        return DATA[start:end]

    def load_chunk(self, start):
        start = (start // 500) * 500
        return {
            "count": 10000000,
            "chunk_size": 500,
            "start": start,
            "data": [make_record(i) for i in range(start, start+500)]
        }


if __name__ == "__main__":
    config_logging("table.log", __file__)
    config = {
        "debug": True,
        "transmitter": "socket",
        "api": API()}
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")
