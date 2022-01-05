import re
from larch.reactive import rule, Pointer, Cell
from ..i18n import pgettext as translate
from ..textlayout import DOMCell, Empty, AlignedCell, Parser, Stretcher, RowSpan, walk_pointer
from ..control import Control, RenderingContext

# __pragma__("skip")
console = document = None
def require(n): pass
# __pragma__ ("noskip")


require("./larch.bo.grid.scss")


class FieldContext(RenderingContext):
    element = Cell()

    def __init__(self, value, parent, cell):
        super().__init__(value, parent)
        self.options["name"] = cell.name
        self.options["id"] = self.parent["id"] + "." + cell.name
        if cell.style:
            self.options["style"] = cell.style


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

        return tmp

    def create(self):
        return {}

    def render(self, grid, grid_element):
        grid.contexts[self.name]["element"] = el = document.createElement("label")
        el.innerHTML = str(translate(self.text))
        self.set_css_style(el.style)
        grid_element.appendChild(el)


class Field(AlignedCell):
    EXPRESSION = re.compile(
        DOMCell.REGEXP
        + "([<>v^]+)?"            # label position
        + r"(\[(.+)\])"           # value_proxy path
        + AlignedCell.REGEXP      # alignment
        + r"(\{(\d*)\})?"         # tabindex
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
        tmp.tabindex = mo.group(8)
        if tmp.tabindex is not None:
            tmp.tabindex = int(tmp.tabindex)
        tmp.view_id = mo.group(10)
        tmp.style = mo.group(12)
        tmp.autofocus = bool(mo.group(13))
        return tmp

    def create(self, grid):
        pointer = Pointer(grid) if self.path.startswith(".") else grid.context.value_pointer
        pointer = walk_pointer(pointer, self.path)
        return FieldContext(pointer, grid.context, self)

    def render(self, grid, grid_element):
        el = document.createElement("div")
        self.set_css_style(el.style)
        grid_element.appendChild(el)
        grid.contexts[self.name].container = el


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

    def render(self, grid, grid_element):
        el = document.createElement("div")
        el.style.width = self.width
        el.style.height = self.height
        self.set_css_style(el.style)
        grid_element.appendChild(el)


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

    layout_cache = {}
    scrollable = False
    fields = []
    element = None

    @property
    def parent(self):
        """returns the parent control"""
        if self.context and self.context.parent:
            return self.context.parent.control

    def _make_cells(self):
        parsed = self.__class__.layout_cache.get(self.layout)
        if parsed is None:
            tindex = 1000
            parsed = {}
            parsed.fields = []
            parsed.cells = {}
            parser = GridParser(self.layout)
            for row in parser.rows:
                for c in row:
                    parsed.cells[c.name] = c
                    if isinstance(c, Field):
                        if c.tabindex is None:
                            c.tabindex = tindex
                            tindex += 1
                        parsed.fields.append(c)

            parsed.fields.sort(lambda c: int(c.tabindex))
            parsed.column_count = parser.column_count
            parsed.row_count = parser.row_count
            parsed.column_stretchers = parser.column_stretchers
            parsed.row_stretchers = parser.row_stretchers
            self.__class__.layout_cache[self.layout] = parsed

        self.fields = parsed.fields
        self.cells = parsed.cells
        self.column_count = parsed.column_count
        self.row_count = parsed.row_count
        self.column_stretchers = parsed.column_stretchers
        self.row_stretchers = parsed.row_stretchers

        self.contexts = {}
        for name, c in self.cells.items():
            ctx = c.create(self)
            if ctx is not None:
                self.contexts[name] = ctx

        self.prepare_contexts()
        return self.cells

    def render(self, parent):
        if not self.context["id"]:
            self.context["id"] = self.__class__.__name__
        self.context.control = self
        el = document.createElement("div")
        el.classList.add("lbo-grid")

        if self.scrollable:
            parent.classList.add("scroll-container")
            parent.classList.add(self.__class__.__name__ + "Container")

        parent.appendChild(el)
        self.render_to_dom(el)
        # when self.element is set, all contexts are initialized
        self.element = el
        self.modify_controls()  # may want to have self.element

    def iter_fields_controls(self):
        for f in self.fields:
            ctx = self.contexts[f.name]
            if ctx and ctx.control is not None:
                yield ctx.control

    def unlink(self):
        super().unlink()
        self.unlink_children()
        self.element.parentElement.classList.remove("scroll-container")
        self.element.parentElement.classList.remove(self.__class__.__name__)
        self.element = None

    def unlink_children(self):
        for ctrl in self.iter_fields_controls():
            ctrl.context.container = None
            ctrl.unlink()

    def render_to_dom(self, element):
        self.unlink_children()
        self._make_cells()
        element.innerHTML = ""
        element.style["grid-template-columns"] = " ".join(
            [f"{c}fr" if c else "auto" for c in self.column_stretchers])
        element.style["grid-template-rows"] = " ".join(
            [f"{c}fr" if c else "auto" for c in self.row_stretchers])

        if sum(self.row_stretchers):
            element.style.height = "100%"
        else:
            element.style.height = ""

        for name, c in self.cells.items():
            c.render(self, element)

    def prepare_contexts(self):
        pass

    def modify_controls(self):
        pass

    def celement(self, name):
        """short for self.contexts[name].control.element"""
        return self.contexts[name].control.element

    def control(self, name):
        """short for self.contexts[name].control"""
        return self.contexts[name].control

    def container(self, name):
        """short for self.contexts[name].container"""
        return self.contexts[name].container

    def get_tab_elements(self):
        elements = []
        for ctrl in self.iter_fields_controls():
            elements.extend(ctrl.get_tab_elements())
        return elements

    @rule
    def _rule_update_cells(self):
        if self.context:
            self.layout
            yield
            if self.element:
                self.render_to_dom(self.element)
                self.modify_controls()


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
