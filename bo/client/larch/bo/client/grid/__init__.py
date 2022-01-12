import re
from larch.reactive import rule, Pointer, Cell
from ..animate import animator
from ..i18n import pgettext as translate
from ..textlayout import DOMCell, Empty, AlignedCell, Parser, RowSpan, Cell as PCell, walk_pointer
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
        self.options["autofocus"] = cell.autofocus
        self.options["id"] = self.parent.get("id") + "." + cell.name
        if cell.style:
            self.options["style"] = cell.style

    def render_to_container(self):
        old_ = self.container.firstChild
        if old_:
            old_.remove()
            tmp = self.container.cloneNode()
            tmp.appendChild(old_)
            self.container.parentElement.appendChild(tmp)
            animator.replace(tmp, self.container)

        self.control.render(self.container)


class Label(AlignedCell):
    EXPRESSION = re.compile(DOMCell.REGEXP + r"([^{}]+)" + AlignedCell.REGEXP)
    text = ""
    control = None

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        tmp.alignment = mo.group(4) or ""
        tmp.name = mo.group(1)
        tmp.text = mo.group(2)
        if tmp.name:
            tmp.name = tmp.name[:-1]  # __:opov
        else:
            tmp.name = tmp.text

        return tmp

    def create_template(self, parent):
        el = document.createElement("label")
        self.set_css_style(el.style)
        parent.appendChild(el)

    def create_context(self):
        return {}

    def render(self, grid, element):
        grid.contexts[self.name]["element"] = element
        element.innerHTML = str(translate("grid", self.text))
        context = grid.contexts[self.field]
        if context:
            context.set("label-element", element)


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
            tmp.name = tmp.name[:-1]   # __:opov
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

    def create_template(self, parent):
        el = document.createElement("div")
        self.set_css_style(el.style)
        parent.appendChild(el)

    def create_context(self, grid):
        pointer = Pointer(grid) if self.path.startswith(".") else grid.context.value_pointer
        pointer = walk_pointer(pointer, self.path)
        return FieldContext(pointer, grid.context, self)

    def render(self, grid, element):
        grid.contexts[self.name].container = element


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

    def create_template(self, parent):
        el = document.createElement("div")
        el.style.width = self.width
        el.style.height = self.height
        self.set_css_style(el.style)
        parent.appendChild(el)

    def create_context(self):
        return

    def render(self, grid, grid_element):
        pass


class Stretcher(PCell):
    EXPRESSION = re.compile(r"<(\d+)([lrtb]?)>")

    def __init__(self, stretch=0, splitter=""):
        self.stretch = stretch
        self.splitter = splitter

    def __repr__(self):
        return f"<{self.stretch}{self.splitter}>"

    @classmethod
    def create_cell(cls, mo):
        return cls(float(mo.group(1)), mo.group(2) or "")


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
    compiled = None
    element = Cell()

    @property
    def parent(self):
        """returns the parent control"""
        if self.context and self.context.parent:
            return self.context.parent.control

    def initialize(self):
        compiled = self.__class__.layout_cache.get(self.layout)
        if compiled is None:
            tindex = 1000
            compiled = {}
            compiled.fields = []
            compiled.cells = {}
            parser = GridParser(self.layout)
            for row in parser.rows:
                for c in row:
                    compiled.cells[c.name] = c
                    if isinstance(c, Field):
                        if c.tabindex is None:
                            c.tabindex = tindex
                            tindex += 1
                        compiled.fields.append(c)

            compiled.fields.sort(lambda c: int(c.tabindex))
            compiled.template = self.create_template(parser, compiled)
            self.layout_to_cache(self.layout, compiled, parser)

        self.compiled = compiled
        self.contexts = {}
        for name, c in compiled.cells.items():
            ctx = c.create_context(self)
            if ctx is not None:
                self.contexts[name] = ctx

        self.prepare_contexts()
        return compiled.template.cloneNode(True)

    def create_template(self, parser, compiled):
        el = document.createElement("div")
        el.classList.add("lbo-grid")
        el.style["grid-template-columns"] = " ".join(
            [f"{c.stretch}fr" if c.stretch else "auto" for c in parser.column_stretchers])
        el.style["grid-template-rows"] = rows = " ".join(
            [f"{c.stretch}fr" if c.stretch else "auto" for c in parser.row_stretchers])
        if "fr" in rows:
            el.style.height = "100%"

        compiled.cells_list = list(compiled.cells.values())
        for c in compiled.cells_list:
            c.create_template(el)

        return el

    def layout_to_cache(self, layout, parsed):
        if "layout" not in self.__reactive_cells__:
            # by default dynamic layouts are not cached
            self.__class__.layout_cache[layout] = parsed

    def render(self, parent):
        if not self.context.get("id"):
            self.context.set("id", self.__class__.__name__)
        self.context.control = self

        # when self.element is set, all contexts are initialized
        self.element = self.render_to_dom(parent)
        self.modify_controls()  # may want to have self.element

    def iter_fields_controls(self):
        for f in self.compiled.fields:
            ctx = self.contexts[f.name]
            if ctx and ctx.control is not None:
                yield ctx.control

    def unlink(self):
        super().unlink()
        self.unlink_children()
        self.element = None

    def unlink_children(self):
        for ctrl in self.iter_fields_controls():
            ctrl.context.container = None
            ctrl.unlink()

    def render_to_dom(self, parent):
        if self.compiled:
            self.unlink_children()
        element = self.initialize()
        parent.appendChild(element)
        for container, c in zip(element.children, self.compiled.cells_list):
            c.render(self, container)
        return element

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
                parent = self.element.parentElement
                parent.innerHTML = ""
                self.render_to_dom(parent)
                self.modify_controls()

    @rule
    def _rule_disabled(self):
        el = self.element
        if el:
            if self.context.observe("disabled"):
                el.classList.add("disabled")
            else:
                el.classList.remove("disabled")


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

    STRETCHER = Stretcher
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

            label.field = c.name
            c.label = label.name
