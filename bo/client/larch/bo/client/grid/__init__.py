import re
from larch.reactive import rule, Pointer, Cell
from ..textlayout import DOMCell, Empty, AlignedCell, Parser, Stretcher, RowSpan, walk_pointer
from ..control import Control, ControlContext, create_control_factory, NullControl
from ..browser import create_element
# from ..tools import ascii_inc


# __pragma__("skip")
def require(n): pass
# __pragma__ ("noskip")


require("./larch.bo.grid.scss")


class FieldContext(ControlContext):
    element = Cell()

    def __init__(self, value, parent, cell):
        super().__init__(value, parent)
        self.options["name"] = cell.name
        self.control = None
        self.old_control_key = None

    def control_key(self):
        t = type(self.value)
        style = self['style']  # __: opov
        return f"{t.__name__}:{t.__module__}-{style}" if t else None

    @rule
    def _rule_render_control(self):
        if self.element is None:
            return

        key = self.control_key()
        if key != self.old_control_key:
            yield
            self.old_control_key = key
            control_factory = create_control_factory(self)
            if control_factory:
                self.control = control_factory(self)
            else:
                self.control = NullControl(self)

            self.control.render(self.element)


class Label(AlignedCell):
    EXPRESSION = re.compile(DOMCell.REGEXP + r"([^{}]+)" + AlignedCell.REGEXP, re.UNICODE)
    text = ""
    control = None

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        tmp.alignment = mo.group(4) or ""
        tmp.text = mo.group(2)

        tmp.name = mo.group(1)
        if tmp.name:
            tmp.name = tmp.name[:-1]
        else:
            tmp.name = tmp.text

        print("create label", tmp.name, tmp.columns, tmp.alignment)
        return tmp

    def create(self):
        return {}

    def render(self, grid):
        grid.contexts[self.name]["element"] = el = create_element("label")
        el.innerHTML = self.text
        self.set_style(el.style)
        grid.element.appendChild(el)


class Field(AlignedCell):
    EXPRESSION = re.compile(
        DOMCell.REGEXP
        + "([<>v^]+)?"            # label position
        + r"(\[(.+)\])"           # value_proxy path
        + AlignedCell.REGEXP      # alignment
        + r"(\{(-?\d*)\})?"       # tabindex
        + r"(#([\w_:.-]+))?"      # dom id
        + r"(@([\w_.-]+))?"       # style
        + "([*]?)")               # autofocus
    label = None

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        tmp.buddy = mo.group(2)
        tmp.path = mo.group(4)

        tmp.name = mo.group(1)
        if tmp.name:
            tmp.name = tmp.name[:-1]
        else:
            tmp.name = tmp.path.split(".")[-1]  # __: opov

        tmp.alignment = mo.group(6) or ""
        try:
            tmp.tabindex = int(mo.group(8) or 0)
        except ValueError:
            tmp.tabindex = None
        tmp.view_id = mo.group(10)
        tmp.style = mo.group(12)
        tmp.autofocus = bool(mo.group(13))
        return tmp

    def create(self, grid):
        pointer = Pointer(grid) if self.path.startswith(".") else grid.context.value_pointer
        return FieldContext(walk_pointer(pointer, self.path), grid.context, self)

    def render(self, grid):
        el = create_element("div")
        self.set_style(el.style)
        grid.element.appendChild(el)
        grid.contexts[self.name].element = el


class Spacer(DOMCell):
    EXPRESSION = re.compile(r"\((.*)\)")
    width = 0
    height = 0

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        spacer = mo.group(1)
        w, h = spacer.split(",")
        tmp.width = w
        tmp.height = h
        return tmp

    def create(self):
        return

    def render(self, grid):
        el = create_element("div")
        el.style.width = self.width
        el.style.height = self.height
        self.set_style(el.style)
        grid.element.appendChild(el)


class Grid(Control):
    """
    Layouts children as grid by a textual description.

    The layout is defined by the attribute "layout"

    A good description must follow here

    Options:
    readonly (in)          sets the document and all children to readonly
    state_to_location (in) if True the layout saves its state into the location. (default: True).
    domain (in)            Translation domain, default: label.
    """
    # TODO: tabindex handling
    # TODO: splitter handling (min(min-content, px)) https://stackoverflow.com/questions/46931103/making-a-dragbar-to-resize-divs-inside-css-grids#46934825

    layout_cache = {}
    element = None

    def _make_cells(self):
        self.cells = self.__class__.layout_cache.get(self.layout)
        if self.cells is None:
            self.cells = {}
            parser = GridParser(self.layout)
            for row in parser.rows:
                for c in row:
                    self.cells[c.name] = c

            self.__class__.layout_cache[self.layout] = self.cells
            self.column_count = parser.column_count
            self.row_count = parser.row_count
            self.column_stretchers = parser.column_stretchers
            self.row_stretchers = parser.row_stretchers

        self.contexts = {}
        for name, c in self.cells.items():
            ctx = c.create(self)
            if ctx is not None:
                self.contexts[name] = ctx

        self.prepare_contexts()
        return self.cells

    def render(self, parent):
        self.element = create_element("div")
        parent.appendChild(self.element)
        self.render_to_dom()

    def render_to_dom(self):
        element = self.element
        element.classList.add("lbo-grid")
        element.style["grid-template-columns"] = " ".join(
            [f"{c}fr" if c else "auto" for c in self.column_stretchers])
        element.style["grid-template-rows"] = " ".join(
            [f"{c}fr" if c else "auto" for c in self.row_stretchers])

        # __pragma__("opov")
        if self.row_stretchers:
            # __pragma__("noopov")
            element.style.height = "100%"

        for name, c in self.cells.items():
            c.render(self)

        self.modify_controls()

    def prepare_contexts(self):
        pass

    def modify_controls(self):
        pass

    @rule
    def _rule_update_cells(self):
        self.layout
        yield
        self._make_cells()
        if self.element:
            self.render_to_dom()


def move(operation, lc, lr):
    for d in operation:
        if d == '<':
            lc -= 1
        elif d == '>':
            lc += 1
        elif d == '^':
            lr -= 1
        elif d == 'v':
            lr += 1
    return lc, lr


class GridParser(Parser):
    """A layout description parser"""

    CELL_TYPES = [Empty, Stretcher, Spacer, Field, RowSpan, Label]

    def __init__(self, layout_string):
        super().__init__(layout_string)
        self.find_buddies()

    def find_buddies(self):
        """
        Set label buddies
        A label buddies is the nearest label left or upper to a field.
        """
        fields = [[c.rows[0], c.columns[0], c]
                  for r in self.rows for c in r if isinstance(c, Field)]
        labels = {f"{c.rows[0]}, {c.columns[0]}": c
                  for r in self.rows for c in r if isinstance(c, Label)}

        for r1, c1, c in fields:
            lr, lc = r1, c1
            if c.buddy:
                lc, lr = move(c.buddy, lc, lr)
            elif f"{lr}, {lc - 1}" in labels:
                lc -= 1
            elif f"{lr - 1}, {lc}" in labels:
                lr -= 1
            else:
                continue

            label = labels.get(f"{lr}, {lc}")
            if label is None:
                continue

            label.control = c
            c.label = label
