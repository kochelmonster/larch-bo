import re
import larch.lib.adapter as adapter
from larch.reactive import Pointer, rule
from itertools import takewhile
from ..i18n import pgettext as translate, HTML
from ..control import Control
from ..textlayout import DOMCell, Empty, AlignedCell, Parser, Stretcher, RowSpan, walk_pointer, Cell


# __pragma__("skip")
console = document = window = Promise = None
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
        name = self.name

        if self.path.startswith(".js."):
            # optimation: direct js access
            attrib = self.path[4:]

            def renderer(element):
                element.innerHTML = grid.convert(name, grid.render_context.value[attrib])
        else:
            pointer = Pointer(grid)
            if not self.path.startswith("."):
                pointer = pointer.render_context.value
            pointer = walk_pointer(pointer, self.path)

            def renderer(element):
                element.innerHTML = grid.convert(name, pointer.__call__())

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
        super().__init__(layout)
        rows = iter(self.rows)
        self.header = list(takewhile(lambda r: len(r), rows))
        self.body = self.rebase_rows(list(takewhile(lambda r: len(r), rows)), len(self.header)+1)
        self.footer = self.rebase_rows(list(rows), len(self.header)+len(self.body)+2)

        console.log("***footer", self.footer)
        if len(self.header) and not len(self.body):
            self.body, self.header = self.header, self.body

    def rebase_rows(self, rows, offset):
        for row in rows:
            for cell in row:
                cell.rows[0] -= offset
                cell.rows[1] -= offset
        return rows


class TemplateBase:
    def __init__(self, template, contexts):
        self.template = template
        self.contexts = contexts


# __pragma__("jscall")
class RowTemplate(TemplateBase):
    SECTION = "b"
    TAG = "div"
    SECTION_TAG = "section"
    BACK = "body"

    def render(self, grid, offset):
        row = grid.render_context.row + offset
        clone = self.template.content.cloneNode(True)
        for el, context in zip(clone.children, self.contexts):
            context.renderer(el)
            el.style.gridRowStart = str(context.rows[0]+row)
            el.style.gridRowEnd = str(context.rows[1]+row+1)
        return clone


class HeaderTemplate(TemplateBase):
    SECTION = "h"
    TAG = "header"
    SECTION_TAG = "header"
    BACK = "header"

    def __init__(self, template, contexts):
        super().__init__(template, contexts)
        self.offset = max([c["rows"][1] for c in contexts]) + 2

    def render_into_viewport(self, grid):
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
        for el in self.elements:
            el.style.position = ""
            el.style.top = ""
            rect = el.getBoundingClientRect()
            el.style.top = (rect.top - top)+"px"
            el.style.position = "sticky"


class FooterTemplate(TemplateBase):
    SECTION = "f"
    TAG = "footer"
    BACK = "footer"
    SECTION_TAG = "footer"

    def render_into_viewport(self, grid, offset):
        clone = RowTemplate.render.call(self, grid, offset)   # jscall!
        self.elements = list(clone.children)
        grid.viewport.appendChild(clone)
        self.update_position(grid)

    def update_position(self, grid):
        bottom = self.elements[0].parentElement.getBoundingClientRect().bottom
        for el in self.elements:
            el.style.position = ""
            el.style.top = ""
            rect = el.getBoundingClientRect()
            el.style.bottom = (bottom - rect.bottom)+"px"
            el.style.position = "sticky"


class DumyTemplate:
    offset = 0

    def render_into_viewport(self, grid):
        pass

# __pragma__("nojscall")


class Table(Control):
    layout_cache = {}
    scrollable = False
    fields = []
    element = None

    def __init__(self, cv):
        super().__init__(cv)
        self.converters = {}  # __:jsiter

    def render(self, parent):
        self.context.control = self
        el = document.createElement("div")
        el.classList.add("lbo-table")
        self.viewport = document.createElement("div")
        el.appendChild(self.viewport)
        parent.appendChild(el)
        self.element = el
        self.provider.ready().then(self.render_to_dom)

    def render_to_dom(self, element):
        provider = self.provider
        viewport = self.viewport
        self.render_context = {}

        self.process_layout()
        viewport.style["grid-template-columns"] = " ".join(
            [f"{c.stretch}fr" if c.stretch else "auto" for c in self.stretchers])

        offset = self.header.render_into_viewport(self)

        count = provider.get_visible_count()
        self.render_context.row = count
        self.footer.render_into_viewport(self, offset)

        self.rows = []
        for i in range(count):
            self.render_context.row = i
            self.render_context.value = provider.get_item(i)
            clone = self.body.render(self, offset)
            self.rows.append(clone.firstChild)
            viewport.appendChild(clone)

    def process_layout(self):
        parser = TableParser(self.layout)
        self.stretchers = parser.column_stretchers
        console.log("***stretchers", self.stretchers)
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
        i = 0
        for row in rows:
            for cell in row:
                element, context = cell.create(self, factory.TAG)
                element.classList.add(f"c{i}", factory.SECTION)
                template.content.appendChild(element)
                contexts.append(context)
                max_row = max(cell.rows[1], max_row)
                i += 1

        area = document.createElement(factory.SECTION_TAG)
        area.classList.add("back")
        area.style.gridColumnStart = "1"
        area.style.gridColumnEnd = str(len(self.stretchers)+1)
        area.style.gridRowStart = "1"
        area.style.gridRowEnd = str(max_row+2)
        template.content.prepend(area)
        contexts.unshift({
            "renderer": getattr(self, "render_" + factory.BACK),
            "rows": [0, max_row]})
        return factory(template, contexts)

    def convert(self, name, value):
        converter = self.converters[name]
        if converter:
            try:
                return converter(value)
            except TypeError:
                pass

        try:
            self.converters[name] = converter = adapter.get(type(value), HTML)(None, self.element)
        except Exception as e:
            console.log("no converter for", value, type(value).__name__, repr(e))
            self.converters[name] = converter = str
        return converter(value)

    def render_header(sef, element):
        pass

    def render_body(self, element):
        pass

    def render_footer(self, element):
        pass

    @rule
    def _rule_update_provider(self):
        value = self.context.value
        style = self.context.get("style")
        for val in self.context.loop('style'):
            style = val
        yield
        if isinstance(value, TableDataProvider):
            self.provider = value.set_table(self)
        else:
            self.provider = adapter.get(type(value), TableDataProvider, style).set_table(self)
        console.log("***set provider", repr(self.provider))


class TableDataProvider:
    def set_table(self, table):
        return self

    def ready(self):
        return Promise.resolve()

    def get_visible_count(self):
        raise NotImplementedError()

    def get_item(self, row):
        raise NotImplementedError()


class ListDataProvider(TableDataProvider):
    def __init__(self, table):
        self.context = table.context

    @classmethod
    def set_table(self, table):
        return ListDataProvider(table)

    def get_visible_count(self):
        return len(self.context.value)

    def get_item(self, row):
        return self.context.value[row]


adapter.register(list, TableDataProvider, "", ListDataProvider)
