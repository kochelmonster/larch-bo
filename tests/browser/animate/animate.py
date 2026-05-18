import ui

# __pragma__("skip")
# ---------------------------------------------------
import sys
import random
import datetime as dt
from larch.lib.test import config_logging
from larch.bo.server import run


def make_record(index):
    return {
        "id_": index,
        "name": f"User {index}",
        "office": f"Office {index % 10}",
        "age": 20 + index % 40,
        "salary": 1000 + (index % 2000),
        "start": dt.date(2024, 1, 1),
        "address": f"Street {index}",
    }


DATA = [make_record(i) for i in range(2000)]


class API:
    def load_data(self, start, end):
        return DATA[start:end]

    def load_chunk(self, start):
        start = (start // 500) * 500
        return {
            "count": len(DATA),
            "chunk_size": 500,
            "start": start,
            "data": DATA[start:start+500],
        }


if __name__ == "__main__":
    config_logging("animate.log", __file__)
    config = {
        "debug": True,
        "transmitter": "socket",
        "api": API(),
    }

    if "--type=test" in sys.argv:
        from test_animate import *  # noqa: F401,F403

    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")
