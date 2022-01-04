from .browser import BODY, get_bubble_attribute


# __pragma__("skip")
class Mock:
    pass


console = Intl = window = navigator = Mock()
def require(n): pass
def __new__(*args): pass
# __pragma__ ("noskip")


window.translations = {}


def get_lang(element=None):
    if element is None:
        element = BODY
    lang = get_bubble_attribute(element, "lang", navigator.language)
    element.lang = lang
    return lang


def gettext(text):
    return window.translations.get(text, text)


def pgettext(context, text):
    return window.translations.get(f"__{context}:{text}", text)


def ngettext(count, singular, plural):
    s, p = window.translation.get(f"++pural:{singular}|{plural}", [singular, plural])
    return p if count != 1 else s


def npgettext(context, count, singular, plural):
    s, p = window.translation.get(f"__{context}:++pural:{singular}|{plural}", [singular, plural])
    return p if count != 1 else s


def label(description):
    def wrapped(func):
        func.__label__ = description
        return func
    return wrapped


def create_number_formatter(style, element=None):
    lang = get_lang(element)
    return __new__(Intl.NumberFormat(lang, style)).format
