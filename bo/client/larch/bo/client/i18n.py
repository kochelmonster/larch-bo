from .browser import BODY, get_bubble_attribute


# __pragma__("skip")
window = navigator = None
def require(n): pass
# __pragma__ ("noskip")


# window.translations = {}


def get_lang():
    return get_bubble_attribute(BODY, "lang", navigator.language)


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
