"""larch browser objects Rendering engine"""
import larch.lib.adapter as adapter
from larch.reactive import Pointer, rcontext, Container, Reactive, Cell, rule
from .browser import BODY


# __pragma__("skip")
document = console = None
def __pragma__(*args): pass
# __pragma__("noskip")


def create_control_factory(context):
    value = context.value
    if isinstance(value, Control):
        value.context = context
        return value

    if value is not None:
        style = context.get("style") or ""
        control_factory = adapter.get(type(value), Control, style)
        if control_factory:
            control = control_factory(context)
            __pragma__("ifdef", "verbose2")
            console.log("create control", repr(value), repr(control))
            __pragma__("endif")
            return control

    console.warn("no control for", value, style, type(value).__name__, repr(context))
    return NullControl(context)


def register(type, style=""):
    def wrap(cls):
        adapter.register(type, Control, style or "", cls)
        return cls
    return wrap


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
        super().unlink()
    # __pragma__("notconv")


class Control(Reactive):
    def __init__(self, context_or_value=None):
        super().__init__()
        if not isinstance(context_or_value, ControlContext):
            context_or_value = ControlContext(context_or_value)
        self.context = context_or_value

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

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
        self.element.innerText = "NULL Control"
        parent.appendChild(self.element)


@register(str, "html")
class HTMLControl(Control):
    """
    Control that displays HTML
    """
    TAG = "div"
    element = Cell()

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)

    def unlink(self):
        self.element = None

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.innerHTML = self.context.value


@register(str, "text")
class TextControl(HTMLControl):
    """
    Control that displays text
    """
    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.innerText = self.context.value


class ControlContext(Reactive):
    _value = Cell()

    # __pragma__ ('kwargs')
    def __init__(self, value=None, parent=None, **kwargs):
        super().__init__()
        self._value = value
        self.parent = parent
        self.options = kwargs
    # __pragma__ ('nokwargs')

    # __pragma__ ('jscall')
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

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.options}>"

    def update_tabindex(self):
        session = self.get("session")
        if session is not None:
            session.update_tabindex()

    def observe(self, name):
        value = self.options.get(name)
        if value is not None:
            if isinstance(value, Container):
                return value.get_value()
        elif self.parent is not None:
            value = self.parent.observe(name)
            if value is not None:
                return value

        if rcontext.inside_rule:
            # transform to container
            self.options[name] = container = Container(value)
            return container.get_value()

        return value

    def get(self, name):
        value = self.options.get(name)
        if value is None and self.parent is not None:
            return self.parent.get(name)

        if isinstance(value, Container):
            return value.get_value()
        return value

    def set(self, name, value):
        val = self.options.get(name)
        if isinstance(val, Container):
            val.set_value(value)
        else:
            self.options[name] = value
        return self
    # __pragma__ ('nojscall')


class RenderingContext(ControlContext):
    container = Cell()

    # __pragma__ ('kwargs')
    def __init__(self, value, parent, **kwargs):
        super().__init__(value, parent, **kwargs)
        self.control = None
        self.old_control_key = None
    # __pragma__ ('nokwargs')

    def control_key(self):
        t = type(self.value)
        style = self.observe('style') or ""
        return f"{t.__name__}:{t.__module__}-{style}" if t else None

    def render_to_container(self):
        self.container.innerHTML = ""
        self.control.render(self.container)

    @rule(-1)
    def _rule_render_control(self):
        if self.container is None:
            return

        key = self.control_key()
        if key != self.old_control_key:
            yield
            if self.control is not None:
                self.control.unlink()
            self.old_control_key = key
            self.control = create_control_factory(self)
            self.render_to_container()
            self.update_tabindex()
