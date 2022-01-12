from larch.reactive import rule
from ..browser import loading_modules, fire_event, save_state
from ..animate import animator
# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("lodash.debounce")

console = document = window = loading_modules
def __pragma__(*args): pass
# __pragma__ ("noskip")


debounce = None
__pragma__('js', '{}', '''
loading_modules.push((async () => {
    debounce = await import('lodash.debounce');
})());
''')


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

        stops = self.get_stops().split(" ")
        self.frs_sum = (window.parseFloat(stops[css_index])
                        + window.parseFloat(stops[css_index+1]))

        split_element.addEventListener("mousedown", self.on_mousedown)
        split_element.style.display = "none"

    @classmethod
    def create_template(cls, index, compiled, template, splitter_template):
        """add spliter information to the compiled object"""
        compiled.splitters.append([cls.__name__, index, template.childElementCount])
        splitter_template.classList.add(cls.SPLITTER_CLASS)
        template.appendChild(splitter_template)

    def on_mousedown(self, event):
        if event.button == 0:
            self.drag_context = {}  # __:jsiter
            self.drag_context.drag_start = self.drag_pos(event)
            self.drag_context.user_select = document.body.style.userSelect
            self.drag_context.cursor_style = document.body.style.cursor
            document.body.style.cursor = window.getComputedStyle(self.split_element).cursor
            document.body.style.userSelect = "none"
            self.prepare_context(self.drag_context)
            document.addEventListener("mousemove", self.on_mousemove)
            document.addEventListener("mouseup", self.on_mouseup)

    def on_mousemove(self, event):
        # console.log("mouse move", event)
        if self.drag_start is not None and event.buttons:
            self.update_grid(self.drag_pos(event), self.drag_context)
            self.update_position()
        else:
            self.on_mouseup(event)

    def on_mouseup(self, event):
        document.removeEventListener("mousemove", self.on_mousemove)
        document.removeEventListener("mouseup", self.on_mouseup)
        document.body.style.userSelect = self.drag_context.user_select
        document.body.style.cursor = self.drag_context.cursor_style
        self.drag_context = self.finish_context(self.drag_context)
        fire_event("state-changed", self.split_element.parentElement, self.index)

    def show(self):
        animator.show(self.split_element, True)
        self.update_position()

    def hide(self):
        animator.show(self.split_element, False)

    def prepare_context(self, context):
        sizes = self.get_calced_stops()
        context.stops = self.get_stops().split(" ")

        min_stops = ["auto" for s in context.stops]
        self.set_stops(min_stops)
        context.min_sizes = self.get_calced_stops()
        self.set_stops(context.stops)

        free_space = self.get_parent_size() - sum(context.min_sizes)
        context.usable_space = free_space * self.usable_space_part
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
        context.stops[self.css_index] = "auto" if frbefore < 0.01 else f"{frbefore}fr"
        context.stops[self.css_index+1] = "auto" if frafter < 0.01 else f"{frafter}fr"
        self.set_stops(context.stops)
        return None

    def update_position(self):
        offset = sum(self.get_calced_stops()[:self.css_index+1])   # __:opov
        self.set_splitter(offset)

    def state(self):
        stops = self.get_stops()
        return [window.parseFloat(stops[self.css_index]),
                window.parseFloat(stops[self.css_index+1])]

    def orect(self):
        return self.split_element.parentElement.getBoundingClientRect()

    def erect(self):
        return self.split_element.getBoundingClientRect()

    def get_calced_stops(self):
        stops = window.getComputedStyle(self.split_element.parentElement)[self.STYLE_NAME]
        return list(map(window.parseFloat, stops.split(" ")))

    def get_stops(self):
        return self.split_element.parentElement.style[self.STYLE_NAME]

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
    HIDE_DELAY = 1000   # ms: hide splitters after this time
    ColSplitter = ColSplitter
    RowSplitter = RowSplitter

    def __init__(self, cv):
        super().__init__(cv)
        self._splitters_visible = False
        self.hide_splitters = debounce(self.hide_splitters, self.HIDE_DELAY)

    def create_template(self, parser, compiled):
        console.log("***create_template", debounce)

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
        super().unlink()
        window.removeEventListener("resize", self._splitter_on_resize)
        window.removeEventListener("mousemove", self.on_show_splitters)

    def _splitter_on_resize(self, event):
        self.hide_splitters()
        self.hide_splitters.flush()

    def splitter_state_changed(self, event):
        self.save_splitter_state()

    def create_splitter_template(self):
        return document.createElement("div")

    def init_splitters(self):
        if len(self.compiled.splitters):
            self.splitters = []
            children = self.element.children
            for i, (cls_name, stop_index, el_index) in enumerate(self.compiled.splitters):
                factory = getattr(self, cls_name)
                self.splitters.append(factory(i, stop_index, children[el_index]))
            window.addEventListener("mousemove", self.on_show_splitters)
            window.addEventListener("resize", self._splitter_on_resize)
            self.element.addEventListener("state-changed", self.splitter_state_changed)

    def on_show_splitters(self, event):
        # console.log("show splitters", event)
        if not self._splitters_visible:
            self._splitters_visible = True
            for s in self.splitters:
                s.show()
        self.hide_splitters()

    def hide_splitters(self):
        self._splitters_visible = False
        for s in self.splitters:
            s.hide()

    def save_splitter_state(self):
        obj = {}  # __:jsiter
        obj.splitters = [s.state() for s in self.splitters]
        save_state(self.context.get(id), obj)

    @rule
    def _rule_init_splitters(self):
        if self.element:
            yield
            self.init_splitters()
