"""larch browser objects Rendering engine"""
import larch.lib.adapter as adapter
from larch.reactive import Pointer, rcontext, Container, Reactive, Cell
from .browser import create_element


def create_control_factory(context):
    value = context.value
    if isinstance(value, Control):
        return value

    style = context["style"]  # __: opov
    return adapter.get(type(value), Control, style or "")


def register(type, style=""):
    def wrap(cls):
        adapter.register(type, Control, style, cls)
        return cls
    return wrap


class Control(Reactive):
    def __init__(self, context_or_value=None):
        super().__init__()
        if not isinstance(context_or_value, ControlContext):
            context_or_value = ControlContext(context_or_value)
        self.context = context_or_value


class NullControl(Control):
    def render(self, parent):
        self.element = create_element("div")
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
