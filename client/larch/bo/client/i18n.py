import larch.lib.adapter as adapter
from .browser import get_bubble_attribute, js_date, js_dom
# __pragma__("ecom")


# __pragma__("skip")
class Mock:
    pass


adapter, js_date, js_dom
document = console = Intl = window = navigator = Date = Mock()
window.lbo = Mock()
def require(n): pass
def __new__(*args): pass
# __pragma__ ("noskip")


class HTML:
    """Used for adapters to register type to html converters"""
    pass


window.lbo.translations = {}


def get_lang(element=None):
    if element is None:
        element = document.body
    lang = get_bubble_attribute(element, "lang", navigator.language)
    element.lang = lang
    return lang


def translate(key, prefix):
    lang = get_lang(document.body)
    table = window.lbo.translations.get(lang, {})
    return table.get(prefix+key, key)


class Translation:
    # __pragma__ ("kwargs")
    def format(self, **kwargs):
        return str(self).format(**kwargs)
    # __pragma__ ("nokwargs")


class Singular(Translation):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.text}>"

    def __str__(self):
        return translate(self.text, "")


class ContextSingular(Translation):
    def __init__(self, context, text):
        self.context = context
        self.text = text

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.context}:{self.text}>"

    def __str__(self):
        return translate(self.text, self.context+"\x04")


class Plural:
    def __init__(self, singular, plural):
        self.singular = singular
        self.plural = plural

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.singular}/{self.plural}>"

    # __pragma__ ("kwargs")
    def format(self, count, **kwargs):
        if count == 1:
            return translate(self.singular).format(**kwargs)
        return translate(self.plural).format(**kwargs)
    # __pragma__ ("nokwargs")


class ContextPlural:
    def __init__(self, context, singular, plural):
        self.context = context
        self.singular = singular
        self.plural = plural

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.context}:{self.singular}/{self.plural}>"

    # __pragma__ ("kwargs")
    def format(self, count, **kwargs):
        if count == 1:
            return translate(self.singular, self.context+"\x04").format(**kwargs)
        return translate(self.plural, self.context+"\x04").format(**kwargs)
    # __pragma__ ("nokwargs")


gettext = Singular
pgettext = ContextSingular
ngettext = Plural
npgettext = ContextPlural


# __pragma__("jsiter")
DEFAULT_NUMBER_STYLE = {
    "notation": "standard",
    "maximumFractionDigits": 2,
    "minimumFractionDigits": 2}

DEFAULT_DATE_STYLE = {
    "month": "2-digit",
    "day": "2-digit",
    "year": "numeric"}
# __pragma__("nojsiter")


def create_number_formatter(style=None, element=None):
    lang = get_lang(element)
    if style is None:
        style = DEFAULT_NUMBER_STYLE
    return __new__(Intl.NumberFormat(lang, style)).format


def create_date_formatter(style=None, element=None):
    lang = get_lang(element)
    if style is None:
        style = DEFAULT_DATE_STYLE
    return __new__(Intl.DateTimeFormat(lang, style)).format


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


def get_date_pattern(locale, style):
    pattern = ""
    formatter = __new__(Intl.DateTimeFormat(locale, {"dateStyle": style}))  # __:jsiter
    result = formatter.formatToParts(__new__(Date(2020, 1, 1)))
    for part in result:
        if part["type"] == "day":
            pattern += "d"
            if len(part.value) == 2:
                pattern += "d"
        elif part["type"] == "month":
            pattern += "M"
            if len(part.value) == 2:
                pattern += "M"
        elif part["type"] == "year":
            pattern += "yy"
            if len(part.value) == 4:
                pattern += "yy"
        elif part["type"] == "literal":
            pattern += part.value
    return pattern


def get_first_day_of_week(locale):
    return 0


def create_number_painter(style=None, element=None):
    format_ = create_number_formatter(style, element)

    def number_painter(dest, value):
        dest.innerText = format_(value)
    return number_painter


def create_date_painter(style=None, element=None):
    format_ = create_date_formatter(style, element)

    def date_painter(dest, value):
        dest.innerText = format_(value)
    return date_painter


def create_str_painter(style=None, element=None):
    def str_painter(dest, value):
        dest.innerText = str(value)
    return str_painter


def create_dom_painter(style=None, element=None):
    def dom_painter(dest, value):
        dest.replaceChildren(value.cloneNode(True))
    return dom_painter


"""?
adapter.register(float, HTML, "", create_number_painter)
adapter.register(js_date, HTML, "", create_date_painter)
adapter.register(str, HTML, "", create_str_painter)
adapter.register(int, HTML, "", create_str_painter)
adapter.register(Translation, HTML, "", create_str_painter)
adapter.register(js_dom, HTML, "", create_dom_painter)
?"""
