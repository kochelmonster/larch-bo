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


def translate(key, prefix):
    lang = get_lang(BODY)
    table = window.translations.get(lang, {})
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


def create_number_formatter(style, element=None):
    lang = get_lang(element)
    return __new__(Intl.NumberFormat(lang, style)).format
