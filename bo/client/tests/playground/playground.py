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

dfns = require("date-fns")


def get_month_names(locale, style):
    months = []  # __:jsiter
    formatter = __new__(Intl.DateTimeFormat(locale, {"month": style}))  # __:jsiter
    for i in range(12):
        result = formatter.formatToParts(__new__(Date(2000, i, 1)))
        months.push(result[0].value)

    return months


def get_week_days(locale, style):
    days = []  # __:jsiter
    formatter = __new__(Intl.DateTimeFormat(locale, {"weekday": style}))  # __:jsiter
    for i in range(7):
        result = formatter.formatToParts(__new__(Date(2020, 1, 10+i)))
        days.push(result[0].value)

    return days


def guess_format(locale, style):
    pattern = ""
    formatter = __new__(Intl.DateTimeFormat(locale, {"dateStyle": style}))  # __:jsiter
    result = formatter.formatToParts(__new__(Date(2020, 1, 1)))
    f = formatter.format(__new__(Date(2020, 1, 1)))
    console.log("result", result, f)
    for part in result:
        if part["type"] == "day":
            pattern += "d"
            if len(part.value) == 2:
                pattern += "d"
        elif part["type"] == "month":
            pattern += "m"
            if len(part.value) == 2:
                pattern += "m"
        elif part["type"] == "year":
            pattern += "yy"
            if len(part.value) == 4:
                pattern += "yy"
        elif part["type"] == "literal":
            pattern += part.value
    return pattern


def get_first_day_of_week(locale):
    pass


def get_i18n_data(locale, date_format=None):
    if date_format is None:
        date_format = guess_format(locale)

    # __pragma__("jsiter")
    return {
        "firstDayOfWeek": get_first_day_of_week(locale),
        "formatDate": lambda date: dfns.format(date_format, date),
        "parseDate": lambda string: dfns.parse(date_format, string),
        "monthNames": get_month_names(locale),
        "weekdays": get_week_days(locale, "long"),
        "weekdaysShort": get_week_days(locale, "short")
        }
    # __pragma__("nojsiter")


m = get_month_names("de", "long")
console.log("months", m)
d = get_week_days("de", "long")
console.log("days", d)
d = get_week_days("de", "short")
console.log("days", d)

pattern = guess_format("de", "medium")
console.log("pattern", pattern)
