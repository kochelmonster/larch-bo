import re
from itertools import takewhile
from larch.reactive import Pointer
from ..i18n import pgettext as translate
from ..textlayout import DOMCell, Empty, AlignedCell, Parser, Stretcher, RowSpan, walk_pointer, Cell

# __pragma__("skip")
console = document = window = Promise = None
# __pragma__ ("noskip")


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
        self.set_css_style(el)
        el.innerHTML = str(translate("table", self.text))
        context = {"renderer": lambda element: None, "rows": self.rows, "name": self.name}
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
        self.set_css_style(el)
        span = document.createElement("span")
        el.appendChild(span)

        name = self.name

        if self.path.startswith(".js."):
            # optimation: direct js access
            attrib = self.path[4:]

            def renderer(element):
                grid.render_value(element.firstChild, name, grid.render_context.value[attrib])

        else:
            pointer = Pointer(grid)
            if not self.path.startswith("."):
                pointer = pointer.render_context.value
            pointer = walk_pointer(pointer, self.path)

            def renderer(element):
                grid.render_value(element.firstChild, name, pointer.__call__())

        context = {"renderer": renderer, "rows": self.rows, "name": self.name}  # __:jsiter
        return el, context


class Selector(AlignedCell):
    EXPRESSION = re.compile(r"[*]" + AlignedCell.REGEXP)

    def __bool__(self):
        return True

    @classmethod
    def create_cell(cls, mo):
        tmp = cls()
        tmp.alignment = mo.group(2) or ""
        return tmp

    def create(self, grid, tag):
        el = document.createElement(tag)
        self.set_css_style(el)
        handler = grid.control_handlers.checkbox(grid)
        handler.create_template(el)
        return el, {"renderer": handler.render, "rows": self.rows, "name": "*"}  # __:jsiter


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
        if len(self.header) and not len(self.body):
            self.body, self.header = self.header, self.body

    def rebase_rows(self, rows, offset):
        for row in rows:
            for cell in row:
                cell.rows[0] -= offset
                cell.rows[1] -= offset
        return rows
