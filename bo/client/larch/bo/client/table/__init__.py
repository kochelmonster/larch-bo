import re
from larch.reactive import Pointer
from itertools import takewhile
from ..i18n import pgettext as translate
from ..control import Control
from ..textlayout import DOMCell, Empty, AlignedCell, Parser, Stretcher, RowSpan, walk_pointer, Cell


# __pragma__("skip")
console = document = window = None
def require(n): pass
def getComputedStyle(e): pass
def parseFloat(n): pass
# __pragma__ ("noskip")


require("./larch.bo.table.scss")


class TreeNode:
    """Mixin for tree nodes"""
    EXPRESSION = "([+])?"


class Label(AlignedCell):
    EXPRESSION = re.compile(
        DOMCell.REGEXP
        + TreeNode.EXPRESSION
        + r"([^{}]+)"  # label text
        + AlignedCell.REGEXP)

    def __repr__(self):
        result = super().__repr__()
        tree = " tree" if self.is_tree else ""
        return result[:-1] + tree + ">"  # __:opov

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        tmp.is_tree = bool(mo.group(2))
        tmp.alignment = mo.group(5) or ""
        tmp.text = mo.group(3)
        tmp.name = mo.group(1)
        if tmp.name:
            tmp.name = tmp.name[:-1]   # __:opov
        else:
            tmp.name = tmp.text
        return tmp

    def create(self, grid, tag):
        el = document.createElement(tag)
        self.set_css_style(el.style)
        el.innerHTML = str(translate("table", self.text))
        context = {"renderer": lambda element: None, "rows": self.rows}
        return el, context


class Content(AlignedCell):
    EXPRESSION = re.compile(
        DOMCell.REGEXP
        + TreeNode.EXPRESSION
        + r"(\[(.*)\])"  # field path
        + AlignedCell.REGEXP)

    def __repr__(self):
        result = super().__repr__()
        tree = " tree" if self.is_tree else ""
        return result[:-1] + tree + ">"  # __:opov

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        tmp.name = mo.group(1)
        tmp.is_tree = bool(mo.group(2))
        tmp.path = mo.group(4)
        tmp.alignment = mo.group(6) or ""
        if tmp.name:
            tmp.name = tmp.name[:-1]
        else:
            tmp.name = tmp.path.split(".")[-1]  # __: opov
        return tmp

    def create(self, grid, tag):
        el = document.createElement(tag)
        self.set_css_style(el.style)

        pointer = Pointer(grid)
        if not self.path.startswith("."):
            pointer = pointer.render_context.value
        pointer = walk_pointer(pointer, self.path)
        name = self.name

        def renderer(element):
            element.innerHTML = grid.transform(name, pointer.__call__())

        context = {"renderer": renderer, "rows": self.rows}
        return el, context


class Selector(Cell):
    @classmethod
    def create_parsed(cls, cell_string, columns):
        if cell_string.strip() == "*":
            r = cls()
            r.columns = columns
            return r
        return None

    def __bool__(self):
        return True

    def create(self, grid, tag):
        el = document.createElement(tag)
        return el, {"renderer": lambda element: None, "rows": self.rows}


class HorzSeparator(Cell):
    EXPRESSION = re.compile(r"-+")

    @classmethod
    def create_cell(cls, mo):
        return cls()


class TableParser(Parser):
    """A layout description parser"""
    CELL_TYPES = (Content, Empty, Selector, HorzSeparator, Stretcher, RowSpan, Label)

    def __init__(self, layout):
        console.log("****parse table layout")
        super().__init__(layout)
        rows = iter(self.rows)
        self.header = list(takewhile(lambda r: len(r), rows))
        self.body = self.rebase_rows(list(takewhile(lambda r: len(r), rows)), len(self.header)+1)
        self.footer = self.rebase_rows(list(rows), len(self.header)+len(self.body)+2)
        if len(self.header) and not len(self.body):
            self.body, self.header = self.header, self.body

    def rebase_rows(self, rows, offset):
        for row in rows:
            for cell in row:
                cell.rows[0] -= offset
                cell.rows[1] -= offset
        return rows


# __pragma__("jscall")
class RowTemplate:
    SECTION = "b"
    TAG = "div"
    BACK = "body"

    def __init__(self, template, contexts):
        self.template = template
        self.contexts = contexts

    def render(self, grid, offset):
        row = grid.render_context.row + offset
        clone = self.template.content.cloneNode(True)
        for el, context in zip(clone.children, self.contexts):
            context.renderer(el)
            el.style.gridRowStart = str(context.rows[0]+row)
            el.style.gridRowEnd = str(context.rows[1]+row+1)
        grid.viewport.appendChild(clone)
        return clone


class HeaderTemplate(RowTemplate):
    SECTION = "h"
    TAG = "header"
    BACK = "header"

    def __init__(self, template, contexts):
        super().__init__(template, contexts)
        self.offset = max([c["rows"][1] for c in contexts]) + 2

    def render(self, grid):
        clone = self.template.content.cloneNode(True)
        self.elements = []
        for el, context in zip(clone.children, self.contexts):
            self.elements.append(el)
            context.renderer(el)
        grid.viewport.appendChild(clone)
        self.update_position(grid)
        return self.offset

    def update_position(self, grid):
        top = self.elements[0].parentElement.getBoundingClientRect().top
        bottom = 0
        for el in self.elements:
            el.style.position = ""
            el.style.top = ""
            rect = el.getBoundingClientRect()
            bottom = max(bottom, rect.bottom - top)
            el.style.top = (rect.top - top)+"px"
            el.style.position = "sticky"


class FooterTemplate(HeaderTemplate):
    SECTION = "f"
    TAG = "footer"
    BACK = "footer"

    def update_position(self):
        bottoms = []
        for el in self.elements:
            rect = el.getBoundingClientRect()
            bottoms.append(rect.bottom)

        console.log("***postion footer")
        offset = max(bottoms) + self.elements[0].parentElement.getBoundingClientRect().height
        for el, bottom in zip(self.elements, bottoms):
            el.style.bottom = (offset - bottom)+"px"
            el.style.position = "sticky"


class DumyTemplate():
    offset = 0

    def render(self, grid):
        pass

# __pragma__("nojscall")


class Table(Control):
    layout_cache = {}
    scrollable = False
    fields = []
    element = None

    def __init__(self, cv):
        super().__init__(cv)

    def render(self, parent):
        self.context.control = self
        el = document.createElement("div")
        el.classList.add("lbo-table")
        self.viewport = document.createElement("div")
        el.appendChild(self.viewport)
        parent.appendChild(el)
        self.render_to_dom(el)
        self.element = el

    def render_to_dom(self, element):
        self.process_layout()
        self.viewport.style["grid-template-columns"] = " ".join(
            [f"{c}fr" if c else "auto" for c in self.stretchers])

        self.render_context = {}
        console.log("***render table")
        offset = self.header.render(self)

        self.rows = []
        for i in range(self.get_visible_count()):
            self.render_context.row = i
            self.render_context.value = self.get_item(i)
            self.rows.append(self.body.render(self, offset))

        self.footer.render(self)

    def process_layout(self):
        parser = TableParser(self.layout)
        self.stretchers = parser.column_stretchers
        self.header = self.create_row_template(parser.header, HeaderTemplate)
        self.body = self.create_row_template(parser.body, RowTemplate)
        self.footer = self.create_row_template(parser.footer, FooterTemplate)

    def create_row_template(self, rows, factory):
        if not len(rows):
            return DumyTemplate()

        console.log("***create template", factory.__name__)

        template = document.createElement("template")
        contexts = []
        max_row = 0
        max_col = 0
        i = 0
        for row in rows:
            for cell in row:
                element, context = cell.create(self, factory.TAG)
                element.classList.add(f"c{i}", factory.SECTION)
                template.content.appendChild(element)
                contexts.append(context)
                max_row = max(cell.rows[1], max_row)
                max_col = max(cell.columns[1], max_col)
                i += 1

        area = document.createElement(factory.TAG)
        area.classList.add("back")
        area.style.gridColumnStart = "1"
        area.style.gridColumnEnd = str(max_col+2)
        area.style.gridRowStart = "1"
        area.style.gridRowEnd = str(max_row+2)
        template.content.prepend(area)
        contexts.unshift({
            "renderer": getattr(self, "render_" + factory.BACK),
            "rows": [0, max_row]})
        return factory(template, contexts)

    def transform(self, name, value):
        return str(value)

    def render_header(sef, element):
        pass

    def render_body(self, element):
        pass

    def render_footer(self, element):
        pass
