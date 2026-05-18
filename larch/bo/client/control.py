"""larch browser objects Rendering engine"""
import larch.lib.adapter as adapter
from larch.reactive import Pointer, Reactive, Cell, rule, untouched, rcontext, atomic
from .browser import fire_event


# __pragma__("skip")
clearInterval = setInterval = document = console = None
def __pragma__(*args): pass

# __pragma__("noskip")


def create_control_factory(context):
    """Resolve a context's value to a Control via the adapter registry."""
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
    """Decorator that registers a control class for a given type and style."""
    def wrap(cls):
        adapter.register(type, Control, style or "", cls)
        return cls
    return wrap


class MixinEventHandler:
    """Mixin for Control"""

    def __init__(self, *args):
        super().__init__(*args)
        self.bound_events = []

    # __pragma__("tconv")
    def fire_event(self, etype, element=None, detail=None, bubbles=False, cancelable=False):
        """Dispatch a custom DOM event."""
        fire_event(etype, element, detail, bubbles, cancelable)

    def handle_event(self, name, listener, capture=False, element=None):
        """Register a DOM event listener and track it for cleanup."""
        if element is None:
            element = document
        element.addEventListener(name, listener, capture)
        self.bound_events.append([name, element, listener])

    def unlink(self):
        """Remove all tracked event listeners."""
        for name, element, listener in self.bound_events:
            element.removeEvent(name, listener)
        super().unlink()
    # __pragma__("notconv")


class Control(Reactive):
    """Base class for all UI controls."""

    def __init__(self, context_or_value=None):
        """Accept a ControlContext or a raw value, which is auto-wrapped."""
        super().__init__()
        if not isinstance(context_or_value, ControlContext):
            context_or_value = ControlContext(context_or_value)
        self.context = context_or_value

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def unlink(self):
        """Cleanup hook for subclasses to release resources."""
        pass

    def get_tab_elements(self):
        """Return focusable elements for tab navigation."""
        return []

    def __ne__(self, other):
        return self is not other


class NullControl(Control):
    """Fallback control rendered when no adapter match is found."""

    def render(self, parent):
        """Render a red placeholder div into the parent element."""
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
        """Create a DOM element and append it to the parent."""
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)

    def unlink(self):
        """Clear the element reference."""
        self.element = None

    @rule
    def _rule_value_changed(self):
        """Reactive rule that syncs innerHTML with the context value."""
        if self.element:
            self.element.innerHTML = self.context.value


@register(str, "text")
class TextControl(HTMLControl):
    """
    Control that displays text
    """
    @rule
    def _rule_value_changed(self):
        """Reactive rule that syncs innerText with the context value."""
        if self.element:
            self.element.innerText = self.context.value


class OptionManager(Reactive):
    """Hierarchical option store with reactive observation support."""

    _observed_changed = Cell(0)
    _last_reactive_round = 0

    def __init__(self):
        self.parent = None
        self.options = {}
        self.observed = {}   # __:jsiter

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.options}>"

    # __pragma__ ('jscall')
    def observe(self, name):
        """Reactively read an option, bubbling to the parent if not found."""
        if rcontext.inside_rule:
            # transform to container
            self._observed_changed   # touch
            self.observed[name] = -1
            value = self.options.get(name)
            if value is None and self.parent is not None:
                return self.parent.observe(name)
            return value
        return self.get(name)

    def loop(self, name):
        """like observer but is a generator that only yields if the value has changed"""
        if rcontext.inside_rule:
            # transform to container
            self._observed_changed   # touch
            value = self.options.get(name)
            if value is None and self.parent is not None:
                self.observed[name] = -1
                return self.parent.loop(name)
            else:
                if name in self.observed:
                    if value is not None and self.observed[name] >= self._last_reactive_round:
                        # the value has changed
                        return [value]
                else:
                    # the first time called
                    self.observed[name] = -1
            return []

        value = self.get(name)
        return [value] if value is not None else []

    def get(self, name):
        """Non-reactive option lookup with parent fallback."""
        value = self.options.get(name)
        if value is None and self.parent is not None:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        """Set an option value and notify reactive observers."""
        self.options[name] = value
        if name in self.observed:
            with atomic(), untouched():
                self.observed[name] = self._last_reactive_round = rcontext.rounds
                self._observed_changed += 1
        return self
    # __pragma__ ('nojscall')


class ControlContext(OptionManager):
    """Option context that holds a reactive value, supporting Pointer indirection."""

    _value = Cell()

    # __pragma__ ('kwargs')
    def __init__(self, value=None, parent=None, **kwargs):
        super().__init__()
        self.parent = parent
        self._value = value
        self.options = kwargs
        self.options.setdefault("style", "")  # never bubble style
    # __pragma__ ('nokwargs')

    # __pragma__ ('jscall')
    @property
    def value(self):
        """The resolved value, dereferencing through a Pointer if present."""
        v = self._value
        if isinstance(v, Pointer):
            return v.__call__()
        return v

    @value.setter
    def value(self, val):
        """Write through the Pointer if present, otherwise set directly."""
        if isinstance(self._value, Pointer):
            self._value.__call__(val)
        else:
            self._value = val

    @property
    def value_pointer(self):
        """Return the underlying Pointer, or wrap the current value in one."""
        v = self._value
        if isinstance(v, Pointer):
            return v
        return Pointer(v)
    # __pragma__ ('nojscall')


class RenderingContext(ControlContext):
    """ControlContext with auto-rendering lifecycle managed by a reactive rule."""

    container = Cell()

    # __pragma__ ('kwargs')
    def __init__(self, value, parent, **kwargs):
        super().__init__(value, parent, **kwargs)
        self.control = None
        self.old_control_key = None
    # __pragma__ ('nokwargs')

    def control_key(self):
        """Compute a cache key from the value's type and current style."""
        t = type(self.value)
        style = self.observe('style') or ""
        return f"{t.__name__}:{t.__module__}-{style}" if t else None

    def render_to_container(self):
        """Clear the container and render the current control into it."""
        self.container.replaceChildren()
        self.control.render(self.container)

    @rule(-1)
    def _rule_render_control(self):
        """Reactive rule that recreates the control when value type or style changes."""
        if self.container is None:
            return

        key = self.control_key()
        if key != self.old_control_key:
            self.old_control_key = key
            yield
            if self.control is not None:
                self.control.unlink()
            self.control = create_control_factory(self)
            self.render_to_container()
            fire_event("update-tabs")


class MixinLiveTracker:
    """A Mixin for live value tracking"""

    TIMER_DELTA = 50
    timer_id = None

    def unlink(self):
        """Stop polling and delegate to super."""
        self.stop_live()
        super().unlink()

    def get_poll_value(self):
        """must be implemented by child class"""
        pass

    def stop_live(self):
        """Cancel the polling interval."""
        if self.timer_id is not None:
            clearInterval(self.timer_id)
            self.timer_id = None

    def live(self):
        """starts live tracking"""
        if self.timer_id is None:
            self._old_value = self.get_poll_value()
            self.timer_id = setInterval(self._poll, self.TIMER_DELTA)
        return self

    def _poll(self):
        """Check for value changes and update the context."""
        value = self.get_poll_value()
        if self._old_value != value:
            self.context.value = self._old_value = value
