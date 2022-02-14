from larch.reactive import rule
from datetime import date
from ...i18n import (
    pgettext, get_lang, get_week_days, get_month_names, get_date_pattern, get_first_day_of_week)
from ...control import Control, register as cregister
from ...browser import loading_modules
from .tools import MixinVaadin, MixinStyleObserver

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update([
    "@vaadin/date-picker", "@vaadin/date-time-picker", "date-fns"])
Date = console = document = loading_modules
def __pragma__(*args): pass
def __new__(*args): pass
# __pragma__("noskip")


dfns = None

__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import('@vaadin/date-picker');
    await import("@vaadin/date-time-picker");
    dfns = await import("date-fns");
})());
''')


def get_i18n_data(locale, date_format=None):
    if date_format is None:
        date_format = get_date_pattern(locale, "medium")

    month_names = get_month_names(locale, "long")
    # __pragma__("jsiter")
    return {
        "calendar": str(pgettext("date", "Calendar")),
        "cancel": str(pgettext("date", "Cancel")),
        "today": str(pgettext("date", "Today")),
        "week": str(pgettext("date", "Week")),
        "firstDayOfWeek": get_first_day_of_week(locale),
        "formatDate": lambda date_: format_date(date_format, date_),
        "parseDate": lambda string: parse_date(date_format, string),
        "formatTitle": lambda month, year: f"{month} {year}",
        "monthNames": month_names,
        "weekdays": get_week_days(locale, "long"),
        "weekdaysShort": get_week_days(locale, "short")
        }
    # __pragma__("nojsiter")


def format_date(format, date_):
    return dfns.format(__new__(Date(date_.year, date_.month, date_.day)), format)


def parse_date(format, string):
    date_ = dfns.parse(string, format, __new__(Date()))
    # __pragma__("jsiter")
    return {
        "year": date_.getFullYear(),
        "month": date_.getMonth(),
        "day": date_.getDay()}
    # __pragma__("nojsiter")


class DatePickerControl(MixinVaadin, MixinStyleObserver, Control):
    TAG = "vaadin-date-picker"

    def render(self, parent):
        el = document.createElement(self.TAG)
        el.i18n = get_i18n_data(get_lang(parent))
        parent.appendChild(el)
        el.inputElement.autocomplete = "nope"  # disable really
        self.element = el
        el.addEventListener("change", self.on_change)
        label = self.context.get("label-element")
        if label:
            label.setAttribute("for", el.inputElement.id)
        self.update_styles()

    def on_change(self, event):
        year, month, day = self.element.value.split("-")
        self.context.value = date(int(year), int(month), int(day))

    @rule
    def _rule_value_changed(self):
        el = self.element
        if el:
            d = self.context.value
            el.value = f"{d._year}-{d._month}-{d._day}"


def register(style=""):
    cregister(date, style)(DatePickerControl)
