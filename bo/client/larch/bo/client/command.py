# __pragma__("skip")
js_undefined = None
# __pragma__("noskip")


def label(prop):
    def wrapped(func):
        func.__label__ = prop
        return func
    return wrapped


def icon(prop):
    def wrapped(func):
        func.__icon__ = prop
        return func
    return wrapped


def ricon(prop):
    def wrapped(func):
        func.__ricon__ = prop
        return func
    return wrapped


def command(prop):
    def wrapped(func):
        func.__command__ = prop
        return func
    return wrapped


def tooltip(prop):
    def wrapped(func):
        func.__tooltip__ = prop
        return func
    return wrapped


def keys(prop):
    def wrapped(func):
        func._keys__ = prop
        return func
    return wrapped


def get_func_prop(func, id_):
    result = func[id_]
    return None if result is js_undefined else result
