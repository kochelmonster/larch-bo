from larch.reactive import rule
# __pragma__("skip")
console = document = window = None
# __pragma__ ("noskip")


class Splitter:
    """Base class for splitters"""

    drag_context = None

    def __init__(self, css_index, dock_element, split_element):
        self.css_index = self.move_css_index(css_index)
        """the index in grid-template-columns/grid-template-rows"""

        self.dock_element = dock_element
        """the dom element, this splitter is docked to"""

        self.split_element = split_element
        """the dom element, of the splitter"""

        split_element.style.display = ""
        self.delta = self.calc_delta(split_element.getBoundingClientRect())
        """half height/width"""
        split_element.style.display = "none"

        console.log("**create splitter", dock_element, split_element, self.delta)

        split_element.addEventListener("mousedown", self.on_mousedown)

    def on_mousedown(self, event):
        console.log("mouse down", event)
        if event.button == 0:
            self.drag_context = {}  # __:jsiter
            self.drag_context.drag_start = self.drag_pos(event)
            self.drag_context.user_select = document.body.style.userSelect
            self.drag_context.cursor = document.body.style.cursor
            document.body.style.cursor = window.getComputedStyle(self.split_element).cursor
            document.body.style.userSelect = "none"
            self.change_to_pixel(self.drag_context)
            self.calc_minsizes(self.drag_context)
            document.addEventListener("mousemove", self.on_mousemove)
            document.addEventListener("mouseup", self.on_mouseup)

    def on_mousemove(self, event):
        # console.log("mouse move", event)
        if self.drag_start is not None and event.buttons:
            self.update_grid(self.drag_pos(event), self.drag_context)
            self.set_position()
            # console.log("***drag", self.split_element.parentElement.style["grid-template-rows"])
        else:
            self.on_mouseup(event)

    def on_mouseup(self, event):
        document.removeEventListener("mousemove", self.on_mousemove)
        document.removeEventListener("mouseup", self.on_mouseup)
        document.body.style.userSelect = self.drag_context.user_select
        document.body.style.cursor = self.drag_context.cursor
        self.drag_context = None
        self.change_to_percent()
        console.log("mouse up", event)

    @classmethod
    def build_template(cls, stretcher, compiled, template):
        """add spliter information to the compiled object"""
        css_index = cls.position(stretcher)

        for i, c in enumerate(compiled.cells_list):
            if cls.position(c) == css_index:
                # Add Splitter information
                # 0: index with grid-column-template/grid-row-template
                # 1: index of dom element the splitter docks to
                # 2: Name Of the splitter class
                # 3: index of the splitter dom element
                compiled.splitters.append([css_index, i, cls.__name__, template.childElementCount])
                template.appendChild(cls.create_splitter())
                return

        console.error("Could not find a docking cell for", css_index, repr(stretcher), cls.__name__)
        raise RuntimeError("no docking cell")

    def show(self):
        style = self.split_element.style
        style.opacity = 0
        style.display = ""
        style.opacity = 1
        self.set_position()

    def hide(self):
        style = self.split_element.style
        style.opacity = 0
        def remove(): style.display = "none"
        window.setTimeout(remove, 205)

    def set_stops(self, before, after):
        self.stops[self.css_index-1] = f"minmax({before}px, auto)"
        self.stops[self.css_index] = f"minmax({after}px, auto)"
        self.set_stop_style(" ".join(self.stops))

    def update_grid(self, pos, context):
        min_delta = context.min_before - context.stops_at_start[0]
        max_delta = context.stops_at_start[1] - context.min_after
        delta = min(max(min_delta, pos - context.drag_start), max_delta)
        before = context.stops_at_start[0] + delta
        after = context.stops_at_start[1] - delta
        self.set_stops(before, after)

    def calc_minsizes(self, context):
        min_stops = ["auto" for s in self.stops]
        self.set_stop_style(" ".join(min_stops))
        calced_stops = list(map(window.parseFloat, self.get_calced_stops().split(" ")))
        console.log("***min_sizes", calced_stops)
        context.min_before = calced_stops[self.css_index-1]
        context.min_after = calced_stops[self.css_index]
        self.set_stop_style(" ".join(self.stops))

    def change_to_pixel(self, context):
        calced_stops = list(map(window.parseFloat, self.get_calced_stops().split(" ")))
        context.stops_at_start = self.template_to_pixel(self.stops, calced_stops)
        context.sum_size = sum(context.stops_at_start)
        context.max_after = context.max_before = context.sum_size
        self.set_stop_style(" ".join(self.stops))

    def change_to_percent(self):
        calced_stops = list(map(window.parseFloat, self.get_calced_stops().split(" ")))
        self.template_to_percent(self.stops, calced_stops)
        console.log("***change_to_percent", self.stops)
        self.set_stop_style(" ".join(self.stops))

    def template_to_percent(self, stops, calced_stops):
        size = sum(calced_stops)
        before = calced_stops[self.css_index - 1]
        stops[self.css_index - 1] = f"minmax({100*before/size}%, 1fr)"
        after = calced_stops[self.css_index]
        stops[self.css_index] = f"minmax({100*after/size}%, 1fr)"

    def template_to_pixel(self, stops, calced_stops):
        before = calced_stops[self.css_index - 1]
        stops[self.css_index - 1] = f"minmax(auto, {before}px)"
        after = calced_stops[self.css_index]
        stops[self.css_index] = f"minmax(auto, {after}px)"
        return [before, after]

    def orect(self):
        return self.dock_element.parentElement.getBoundingClientRect()

    def erect(self):
        return self.dock_element.getBoundingClientRect()


class Left:
    @classmethod
    def position(cls, cell):
        return cls.span(cell)[0] + 1

    def move_css_index(self, css_index):
        """normalize the css_index"""
        return css_index - 1


class Right:
    @classmethod
    def position(cls, cell):
        return cls.span(cell)[1] + 2

    def move_css_index(self, css_index):
        """normalize the css_index"""
        return css_index


class RowSplitter(Splitter):
    @classmethod
    def create_template(cls, stretcher, compiled, template):
        if stretcher.splitter == "t":
            return TopSplitter.build_template(stretcher, compiled, template)
        return BottomSplitter.build_template(stretcher, compiled, template)

    @classmethod
    def span(cls, cell):
        return cell.rows

    @classmethod
    def create_splitter(self):
        el = document.createElement("div")
        el.classList.add("h-splitter")
        return el

    def offset(self):
        return self.orect().top

    def calc_delta(self, rect):
        return rect.height / 2

    def drag_pos(self, event):
        return event.clientY

    def init_col_templates(self, columns, calced_columns):
        pass

    def init_row_template(self, rows, calced_rows):
        self.template_to_percent(rows, calced_rows)
        self.stops = rows

    def get_calced_stops(self):
        return window.getComputedStyle(self.split_element.parentElement)["grid-template-rows"]

    def set_stop_style(self, stops):
        self.split_element.parentElement.style["grid-template-rows"] = stops


class ColSplitter(Splitter):
    @classmethod
    def create(cls, stretcher, compiled, template):
        if stretcher.splitter == "t":
            return LeftSplitter.build_template(stretcher, compiled, template)
        return RightSplitter.build_template(stretcher, compiled, template)

    def span(self, cell):
        return cell.columns

    def create_splitter(self):
        el = document.createElement("div")
        el.classList.add("v-splitter")
        return el

    def offset(self):
        return self.orect().left

    def calc_delta(self, rect):
        return rect.width / 2

    def drag_pos(self, event):
        return event.clientX

    def init_row_template(self, rows, calced_rows):
        pass

    def init_col_templates(self, columns, calced_columns):
        self.template_to_percent(columns, calced_columns)
        self.stops = columns

    def get_calced_stops(self):
        return window.getComputedStyle(self.split_element.parentElement)["grid-template-columns"]

    def set_stop_style(self, stops):
        self.split_element.parentElement.style["grid-template-columns"] = stops


class TopSplitter(Left, RowSplitter):
    def set_position(self):
        self.split_element.style.top = self.erect().top - self.offset() - self.delta + "px"


class BottomSplitter(Right, RowSplitter):
    def set_position(self):
        self.split_element.style.top = window.getComputedStyle(self.dock_element).bottom


class LeftSplitter(Left, ColSplitter):
    def set_position(self):
        self.split_element.style.left = window.getComputedStyle(self.dock_element).left


class RightSplitter(Right, ColSplitter):
    def set_position(self):
        self.split_element.style.left = window.getComputedStyle(self.dock_element).right


class MixinSplitter:
    """
    A Mixin for grid, to support splitter.
    """
    TopSplitter = TopSplitter
    BottomSplitter = BottomSplitter
    LeftSplitter = LeftSplitter
    RightSplitter = RightSplitter
    _splitter_visible = 0

    def create_template(self, parser, compiled):
        compiled.splitters = []
        template = super().create_template(parser, compiled)
        for s in parser.column_stretchers:
            if s.splitter:
                ColSplitter.create_template(s, compiled, template)

        for s in parser.row_stretchers:
            if s.splitter:
                RowSplitter.create_template(s, compiled, template)

        return template

    def init_splitters(self):
        if len(self.compiled.splitters):
            self.splitters = []
            children = self.element.children
            for css_index, el_index, factory, split_index in self.compiled.splitters:
                factory = getattr(self, factory)
                self.splitters.append(factory(css_index, children[el_index], children[split_index]))
            self.element.addEventListener("mousemove", self.on_show_splitters)

            style = self.element.style
            columns = style["grid-template-columns"].split(" ")
            rows = style["grid-template-rows"].split(" ")
            style = window.getComputedStyle(self.element)
            calced_columns = list(map(window.parseFloat, style["grid-template-columns"].split(" ")))
            calced_rows = list(map(window.parseFloat, style["grid-template-rows"].split(" ")))
            for s in self.splitters:
                s.init_col_templates(columns, calced_columns)
                s.init_row_template(rows, calced_rows)

            self.element.style["grid-template-columns"] = " ".join(columns)
            self.element.style["grid-template-rows"] = " ".join(rows)

    def unlink(self):
        if self._splitter_visible:
            window.clearTimeout(self._splitter_visible)
        super().unlink()

    def on_show_splitters(self, event):
        # console.log("show splitters", event)
        if not self._splitter_visible:
            self._splitter_visible = window.setTimeout(self.hide_splitters, 2000)
            for s in self.splitters:
                s.show()

    def hide_splitters(self):
        return
        self._splitter_visible = 0
        for s in self.splitters:
            s.hide()

    @rule
    def _rule_init_splitters(self):
        if self.element:
            yield
            self.init_splitters()
