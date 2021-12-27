"""larch browser objects Rendering engine"""
import larch.lib.adapter as adapter
from larch.reactive import Pointer, rcontext, Container, Reactive, Cell


# __pragma__("skip")
document = None
def __pragma__(*args): pass
# __pragma__("noskip")


def create_control_factory(context):
    value = context.value
    if isinstance(value, Control):
        value.context = context
        return value

    style = context["style"]  # __: opov
    control_factory = adapter.get(type(value), Control, style or "")
    if control_factory:
        return control_factory(context)

    return NullControl(context)


def register(type, style=""):
    def wrap(cls):
        adapter.register(type, Control, style, cls)
        return cls
    return wrap


BODY = None


def set_body():
    global BODY
    BODY = document.querySelector("body")


# __pragma__ ('ecom')
"""?
document.addEventListener('DOMContentLoaded', set_body)
?"""


class EventHandler:
    """Mixin for Control"""

    def __init__(self, *args):
        super().__init__(*args)
        self.bound_events = []

    # __pragma__("tconv")
    def fire_event(self, etype, bubbles=False, cancelable=False, detail=None, element=None):
        if element is None:
            element = BODY

        __pragma__('js', '{}', '''
            var options = {
                bubbles: bubbles,
                cancelable: cancelable,
                detail: detail };
            element.dispatchEvent(new CustomEvent(etype, options));
        ''')

    def handle_event(self, name, listener, capture=False, element=None):
        if element is None:
            element = BODY
        element.addEventListener(name, listener, capture)

    def unlink(self):
        for name, element, listener in self.bound_events:
            element.removeEvent(name, listener)
    # __pragma__("notconv")


class Control(Reactive):
    def __init__(self, context_or_value=None):
        super().__init__()
        if not isinstance(context_or_value, ControlContext):
            context_or_value = ControlContext(context_or_value)
        self.context = context_or_value

    def unlink(self):
        pass

    def get_tab_elements(self):
        return []

    def __ne__(self, other):
        return self is not other


class NullControl(Control):
    def render(self, parent):
        self.element = document.createElement("div")
        self.element.style.backgroundColor = "red"
        self.element.innerText = "NULL"
        parent.appendChild(self.element)


class ControlContext(Reactive):
    _value = Cell()

    # __pragma__ ('kwargs')
    def __init__(self, value=None, parent=None, **kwargs):
        super().__init__()
        self._value = value
        self.parent = parent
        self.options = kwargs
    # __pragma__ ('nokwargs')

    @property
    def value(self):
        v = self._value
        if isinstance(v, Pointer):
            return v.__call__()
        return v

    @value.setter
    def value(self, val):
        if isinstance(self._value, Pointer):
            self._value.__call__(val)
        else:
            self._value = val

    @property
    def value_pointer(self):
        v = self._value
        if isinstance(v, Pointer):
            return v
        return Pointer(v)

    def __getitem__(self, name):
        value = self.options.get(name)
        if value:
            if isinstance(value, Container):
                return value.get_value()

            if rcontext.inside_rule:
                # transform to container
                self.options[name] = container = Container(value)
                return container.get_value()
        elif self.parent is not None:
            return self.parent[name]  # __: opov

        return value

    def __setitem__(self, name, value):
        val = self.options.get(name)
        if isinstance(val, Container):
            val.set_value(value)
        else:
            self.options[name] = value
