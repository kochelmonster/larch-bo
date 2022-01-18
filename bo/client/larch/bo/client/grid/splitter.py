from larch.reactive import rule
from ..browser import loading_modules, fire_event
from ..animate import animator
from ..js.debounce import debounce
# __pragma__("skip")
console = document = window = __new__ = ResizeObserver = loading_modules
def __pragma__(*args): pass
# __pragma__ ("noskip")


class Splitter:
    """Base class for splitters"""

    drag_context = None

    def __init__(self, index, css_index, split_element):
        split_element.style.display = ""

        self.index = index
        """The index within the splitter array"""

        self.css_index = css_index
        """index in the grid-template-xxx style"""

        self.split_element = split_element
        """the dom element, of the splitter"""

        self.move_offset = self.calc_move_offset(split_element.getBoundingClientRect())
        """half height/width"""

        stops = self.get_stops()
        self.frs_sum = (window.parseFloat(stops[css_index])
                        + window.parseFloat(stops[css_index+1]))

        split_element.addEventListener("pointerdown", self.on_mousedown)
        split_element.style.display = "none"

    @classmethod
    def create_template(cls, index, compiled, template, splitter_template):
        """add spliter information to the compiled object"""
        compiled.splitters.append([cls.__name__, index, template.childElementCount])
        splitter_template.classList.add(cls.SPLITTER_CLASS)
        template.appendChild(splitter_template)

    def on_mousedown(self, event):
        if event.button == 0 and event.buttons:
            self.drag_context = {}  # __:jsiter
            self.drag_context.drag_start = self.drag_pos(event)
            self.drag_context.user_select = document.body.style.userSelect
            self.drag_context.cursor_style = document.body.style.cursor
            document.body.style.cursor = window.getComputedStyle(self.split_element).cursor
            document.body.style.userSelect = "none"
            self.prepare_context(self.drag_context)
            document.body.setPointerCapture(event.pointerId)
            document.addEventListener("pointermove", self.on_mousemove)
            document.addEventListener("pointerup", self.on_mouseup)
            document.addEventListener("pointercancel", self.on_mouseup)
            event.preventDefault()

    def on_mousemove(self, event):
        if self.drag_start is not None and event.buttons:
            self.update_grid(self.drag_pos(event), self.drag_context)
            self.update_position()
            event.preventDefault()
        else:
            self.on_mouseup(event)

    def on_mouseup(self, event):
        document.body.releasePointerCapture(event.pointerId)
        document.removeEventListener("pointermove", self.on_mousemove)
        document.removeEventListener("pointerup", self.on_mouseup)
        document.removeEventListener("pointercancel", self.on_mouseup)
        document.body.style.userSelect = self.drag_context.user_select
        document.body.style.cursor = self.drag_context.cursor_style
        self.drag_context = self.finish_context(self.drag_context)
        fire_event("state-changed", self.split_element.parentElement, self.index)
        event.preventDefault()

    def show(self):
        animator.show(self.split_element, True)
        self.update_position()

    def hide(self):
        animator.show(self.split_element, False)

    def prepare_context(self, context):
        sizes = self.get_calced_stops()
        context.stops = self.get_stops()

        min_stops = ["auto" for s in context.stops]
        self.set_stops(min_stops)
        context.min_sizes = self.get_calced_stops()
        self.set_stops(context.stops)

        context.before = context.before_start = sizes[self.css_index]
        context.after = context.after_start = sizes[self.css_index+1]
        context.min_before = context.min_sizes[self.css_index]
        context.min_after = context.min_sizes[self.css_index+1]
        context.min_delta = context.min_before - context.before
        context.max_delta = context.after - context.min_after

    def update_grid(self, pos, context):
        delta = min(max(pos - context.drag_start, context.min_delta), context.max_delta)
        context.before = context.before_start + delta
        context.after = context.after_start - delta
        context.stops[self.css_index] = context.before+"px"
        context.stops[self.css_index+1] = context.after+"px"
        self.set_stops(context.stops)

    def finish_context(self, context):
        pbefore = context.before/(context.before_start+context.after_start)
        frbefore = pbefore * self.frs_sum
        frafter = (1-pbefore) * self.frs_sum
        context.stops[self.css_index] = f"{frbefore}fr"
        context.stops[self.css_index+1] = f"{frafter}fr"
        self.set_stops(context.stops)
        return None

    def update_position(self):
        offset = sum(self.get_calced_stops()[:self.css_index+1])   # __:opov
        self.set_splitter(offset)

    def get_state(self):
        stops = self.get_stops()
        return [stops[self.css_index], stops[self.css_index+1]]

    def set_state(self, state):
        stops = self.get_stops()
        stops[self.css_index] = state[0]
        stops[self.css_index+1] = state[1]
        self.set_stops(stops)

    def orect(self):
        return self.split_element.parentElement.getBoundingClientRect()

    def erect(self):
        return self.split_element.getBoundingClientRect()

    def get_calced_stops(self):
        stops = window.getComputedStyle(self.split_element.parentElement)[self.STYLE_NAME]
        return list(map(window.parseFloat, stops.split(" ")))

    def get_stops(self):
        return self.split_element.parentElement.style[self.STYLE_NAME].split(" ")

    def set_stops(self, stops):
        self.split_element.parentElement.style[self.STYLE_NAME] = " ".join(stops)


class RowSplitter(Splitter):
    STYLE_NAME = "grid-template-rows"
    SPLITTER_CLASS = "h-splitter"

    def set_splitter(self, offset):
        self.split_element.style.top = offset - self.move_offset+"px"

    def calc_move_offset(self, rect):
        return rect.height / 2

    def drag_pos(self, event):
        return event.clientY

    def get_parent_size(self):
        return self.orect().height


class ColSplitter(Splitter):
    STYLE_NAME = "grid-template-columns"
    SPLITTER_CLASS = "v-splitter"

    def set_splitter(self, offset):
        self.split_element.style.left = offset - self.move_offset+"px"

    def calc_move_offset(self, rect):
        return rect.width / 2

    def drag_pos(self, event):
        return event.clientX

    def get_parent_size(self):
        return self.orect().width


def find_splitters(stretchers):
    # __pragma__("opov")
    # i + 1 because grid-template is one based
    return [i for i, (b, a) in enumerate(zip(stretchers[:-1], stretchers[1:]))
            if b.splitter and a.splitter]
    # __pragma__("noopov")


class MixinSplitter:
    """
    A Mixin for grid, to support splitter.
    """
    HIDE_DELAY = 2000   # ms: hide splitters after this time
    ColSplitter = ColSplitter
    RowSplitter = RowSplitter

    def __init__(self, cv):
        super().__init__(cv)
        self._splitters_visible = False
        self.hide_splitters = debounce(self.hide_splitters, self.HIDE_DELAY)

    def create_template(self, parser, compiled):
        compiled.splitters = []
        template = super().create_template(parser, compiled)

        for index in find_splitters(parser.column_stretchers):
            splitter = self.create_splitter_template()
            ColSplitter.create_template(index, compiled, template, splitter)

        for index in find_splitters(parser.row_stretchers):
            splitter = self.create_splitter_template()
            RowSplitter.create_template(index, compiled, template, splitter)

        return template

    def unlink(self):
        window.removeEventListener("pointermove", self.on_show_splitters)
        window.removeEventListener("touchdown", self.on_show_splitters)
        self.resize_observer.unobserve(self.element)
        super().unlink()

    def _on_splitter_resize(self, entries):
        self.hide_splitters()
        self.hide_splitters.flush()

    def splitter_state_changed(self, event):
        window.lbo.state.set(
            self.context.get("id"), "splitter", [s.get_state() for s in self.splitters])

    def create_splitter_template(self):
        outer = document.createElement("div")
        outer.appendChild(document.createElement("div"))
        return outer

    def init_splitters(self):
        if len(self.compiled.splitters):
            self.splitters = []
            children = self.element.children
            for i, (cls_name, stop_index, el_index) in enumerate(self.compiled.splitters):
                factory = getattr(self, cls_name)
                self.splitters.append(factory(i, stop_index, children[el_index]))
            window.addEventListener("pointermove", self.on_show_splitters)
            window.addEventListener("touchdown", self.on_show_splitters)
            self.element.addEventListener("state-changed", self.splitter_state_changed)
            self.resize_observer = __new__(ResizeObserver(self._on_splitter_resize))
            self.resize_observer.observe(self.element)

    def on_show_splitters(self, event):
        if not self._splitters_visible:
            self._splitters_visible = True
            for s in self.splitters:
                s.show()
        self.hide_splitters()

    def hide_splitters(self):
        self._splitters_visible = False
        for s in self.splitters:
            s.hide()

    @rule
    def _rule_init_splitters(self):
        if self.element:
            yield
            self.init_splitters()

    @rule
    def _rule_update_splitter_state(self):
        if self.element:
            yield
            for state in window.lbo.state.loop(self.context.get("id"), "splitter"):
                for state, splitter in zip(state, self.splitters):
                    splitter.set_state(state)
