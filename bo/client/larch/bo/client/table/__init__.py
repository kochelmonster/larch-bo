"""
A vitrual tree table based on  css grid

The veritcal Layout of the grid:
+---------------------------------------+
| header (sticky, optional)             |
+---------------------------------------+
| upper scroll padding                  |
+---------------------------------------+
| body                                  | <-- display block
+---------------------------------------+
| lower scroll padding                  |
+---------------------------------------+
| empty  (1fr)                          |
+---------------------------------------+
| footer (sticky, optional)             |
+---------------------------------------+

the empty row is responsible to place the footer at the bootom of the containing cell
if the table is vertically stretched.
"""

import larch.lib.adapter as adapter
from larch.reactive import rule, Cell, Reactive
from ..i18n import HTML
from ..control import Control
from ..browser import get_metrics
from .parser import TableParser
from .provider import TableDataProvider


# __pragma__("skip")
console = document = window = None
def require(n): pass
def __pragma__(**args): pass
# __pragma__ ("noskip")


require("./larch.bo.table.scss")


class Table(Control):
    STATIC_LIMIT = 200   # below this row_count no virtual list
    element = None
    updated = Cell(0)

    def __init__(self, cv):
        super().__init__(cv)
        self.value_painters = {}  # __:jsiter
        self.render_context = {}  # __:jsiter
        self.anchor = {"row": 0, "offset": 0}  # __:jsiter
        """a visible row with its distance from the viewports top"""

        self.row_start = self.row_end = 0
        """the row range of the display_block"""

        self.virtual_mode = False
        """If True, the table operates in virtual mode"""

        self.block_size = 0
        """the count of rows inside the display block"""

        self.rows = []

    def render(self, parent):
        self.context.control = self
        el = document.createElement("div")
        el.classList.add("lbo-table")
        self.viewport = document.createElement("div")
        el.appendChild(self.viewport)
        parent.appendChild(el)

        self.process_layout()
        self.reset_widths()

        self.header.complete_template(self.viewport)
        self.footer.complete_template(self.viewport)

        el.table = self   # debug
        self.element = el
        self.render_frame()
        self.start_provider()

    def reset_widths(self):
        self.viewport.style["grid-template-columns"] = " ".join(
            [f"{c.stretch}fr" if c.stretch else "auto" for c in self.stretchers])

    def process_layout(self):
        parser = TableParser(self.layout)
        self.stretchers = parser.column_stretchers
        self.header = self.create_row_template(parser.header, HeaderTemplate)
        self.body = self.create_row_template(parser.body, RowTemplate)
        self.footer = self.create_row_template(parser.footer, FooterTemplate)

    def create_row_template(self, rows, factory):
        if not len(rows):
            return DumyTemplate()

        template = document.createElement("template")
        contexts = []
        max_row = 0
        i = 0
        for row in rows:
            for cell in row:
                element, context = cell.create(self, factory.TAG)
                element.classList.add(f"c{i}", factory.SECTION)
                element.lbo_col = i
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
            "renderer": getattr(self, "render_" + factory.BACK), "rows": [0, max_row]})
        return factory(template, contexts)

    def render_frame(self):
        viewport = self.viewport
        viewport.replaceChildren()

        upper_rows = (self.header.row_count   # header
                      + 1                     # upper scroll padding
                      + 1                     # body
                      + 1)                    # lower scroll padding

        viewport.style["grid-template-rows"] = (
            f"repeat({upper_rows}, auto) 1fr repeat({self.footer.row_count}, auto)")

        self.header.render_into_viewport(self)

        offset = self.header.row_count + 1   # one based
        self.upper_scroll = document.createElement("div")
        self.upper_scroll.classList.add("scroll-padding")
        self.upper_scroll.style.gridColumnStart = "1"
        self.upper_scroll.style.gridColumnEnd = str(len(self.stretchers)+1)
        self.upper_scroll.style.gridRowStart = str(offset)
        self.upper_scroll.style.gridRowEnd = str(offset+1)
        self.upper_scroll.lbo_row = -3
        self.viewport.appendChild(self.upper_scroll, self.viewport.firstChild)

        offset = -(self.footer.row_count + 2)
        self.lower_scroll = document.createElement("div")
        self.lower_scroll.classList.add("scroll-padding")
        self.lower_scroll.style.gridColumnStart = "1"
        self.lower_scroll.style.gridColumnEnd = str(len(self.stretchers)+1)
        self.lower_scroll.style.gridRowStart = str(offset-1)
        self.lower_scroll.style.gridRowEnd = str(offset)
        self.lower_scroll.lbo_row = -3
        self.viewport.appendChild(self.lower_scroll)
        self.footer.render_into_viewport(self)

    def set_row_count(self, count):
        self.row_count = count
        if count < self.STATIC_LIMIT:
            self.block_size = count  # still performant
        else:
            metrics = get_metrics()
            self.block_size = int(2 * window.screen.height / metrics.line_height)
            # enough to cover the screen

        upper_rows = (self.header.row_count   # header
                      + 1                     # upper scroll spanner
                      + count                 # body
                      + 1)                    # lower scroll spanner
        self.viewport.style["grid-template-rows"] = (
            f"repeat({upper_rows}, auto) 1fr repeat({self.footer.row_count}, auto)")

        self.virtual_mode = False
        self.update_display()

        self.virtual_mode = self.row_start > 0 or self.row_end < self.row_count
        if self.virtual_mode:
            # virtual mode
            self.element.addEventListener("scroll", self.on_scroll)
            self.columns = window.getComputedStyle(self.viewport)["grid-template-columns"]

            # we estimate the row height from the first rows
            display_height = sum([section.getBoundingClientRect().height for section in self.rows])
            self.row_height = display_height / (self.row_end - self.row_start)

            # change block_size to a more suitable value
            self.block_size = int(2.5 * window.screen.height / self.row_height)
            self.virtual_scroll_space = self.row_height * self.row_count
            self.update_display()
        else:
            self.element.removeEventListener("scroll", self.on_scroll)

    def update_data(self):
        # delete complete display_block
        element = self.upper_scroll.nextSibling
        while 0 <= element.lbo_row:
            element.remove()
            element = self.upper_scroll.nextSibling

        data = self.provider.request(self.row_start, self.row_end)
        self.render_display_block(data, self.row_start)
        self.rows = self.element.querySelectorAll("section")

        if self.virtual_mode:
            self.update_scrollbar()

        self.update_anchor()
        self.updated += 1

    def update_display(self):
        self.row_start = max(self.anchor.row - self.block_size//2, 0)
        self.row_end = min(self.row_start + self.block_size, self.row_count)
        self.row_start = max(self.row_end - self.block_size, 0)

        # delete all before row_start
        element = self.upper_scroll.nextSibling
        while 0 <= element.lbo_row < self.row_start:
            element.remove()
            element = self.upper_scroll.nextSibling

        # delete all after row_end
        element = self.lower_scroll.previousSibling
        while element.lbo_row >= self.row_end:
            element.remove()
            element = self.lower_scroll.previousSibling

        changed_display = False

        # insert rows after row_start
        element = self.upper_scroll.nextSibling
        if element.lbo_row > self.row_start:
            data = self.provider.request(self.row_start, element.lbo_row)
            self.render_display_block(data, self.row_start)
            changed_display = True

        # insert rows before row_end
        element = self.lower_scroll.previousSibling
        if element.lbo_row < self.row_end - 1:
            start = max(self.row_start, element.lbo_row + 1)
            data = self.provider.request(start, self.row_end)
            self.render_display_block(data, start)
            changed_display = True

        if changed_display:
            self.rows = self.element.querySelectorAll("section")

        if self.virtual_mode:
            columns = window.getComputedStyle(self.viewport)["grid-template-columns"]
            if columns != self.columns:
                self.columns = columns
                columns = columns.split(" ")
                tmp = []
                for size, c in zip(columns, self.stretchers):
                    tmp.append(f"{c.stretch}fr" if c.stretch else f"minmax({size}, auto)")
                self.viewport.style["grid-template-columns"] = " ".join(tmp)

            self.update_scrollbar()

        self.update_anchor()
        self.updated += 1

    def update_scrollbar(self):
        real_height = sum([section.getBoundingClientRect().height for section in self.rows])
        virtual_height = self.row_height * self.rows.length
        delta = virtual_height - real_height

        top_section = self.rows[0]
        anchor = self.rows[self.anchor.row - self.row_start]

        # inside the display block
        scroll_pos = (anchor.getBoundingClientRect().top
                      - top_section.getBoundingClientRect().top
                      - self.anchor.offset)
        relation = scroll_pos / (real_height-self.element.getBoundingClientRect().height)
        relation = max(0, min(1, relation))

        upper_space = self.row_start * self.row_height + delta * relation
        lower_space = (self.row_count - self.row_end) * self.row_height + delta * (1-relation)
        self.upper_scroll.style.height = upper_space + "px"
        self.lower_scroll.style.height = lower_space + "px"

        # scroll the anchor to the correct position
        rect = self.element.getBoundingClientRect()
        aoffset = anchor.getBoundingClientRect().top - rect.top - self.header.height
        delta_scroll = aoffset - self.anchor.offset
        if delta_scroll:
            self.element.removeEventListener("scroll", self.on_scroll)
            self.element.scrollTop += delta_scroll
            self.element.addEventListener("scroll", self.on_scroll)

        self._no_scroll -= 1

    def update_anchor(self):
        rect = self.element.getBoundingClientRect()
        anchor = self.find_anchor_section(rect)
        self.anchor.row = anchor.lbo_row
        self.anchor.offset = anchor.getBoundingClientRect().top-rect.top-self.header.height

    def render_display_block(self, data, start):
        viewport = self.viewport
        pivot = self.upper_scroll.nextSibling if start == self.row_start else self.lower_scroll

        offset = (self.header.row_count + 1   # one based
                  + 1)                        # upper scroll spanner

        for index, val in enumerate(data):
            self.render_context.row = index + start
            self.render_context.value = val
            clone = self.body.render(self, offset)
            viewport.insertBefore(clone, pivot)

    def render_value(self, element, name, value):
        painter = self.value_painters[name]
        if painter:
            try:
                painter(element, value)
                return
            except TypeError:
                pass

        try:
            self.value_painters[name] = painter = adapter.get(type(value), HTML)(None, self.element)
        except Exception as e:
            console.log("no converter for", value, type(value).__name__, repr(e))
            self.value_painters[name] = painter = adapter.get(str, HTML)(None, self.element)
        painter(element, value)

    def render_header(self, element):
        """can be used to change the element"""
        pass

    def render_body(self, element):
        """can be used to change the element"""
        pass

    def render_footer(self, element):
        """can be used to change the element"""
        pass

    def on_scroll(self):
        if not self._scroll_pending:
            self._scroll_pending = True
            window.requestAnimationFrame(self.throttled_scroll)

    def throttled_scroll(self):
        scroll_top = self.element.scrollTop
        rect = self.element.getBoundingClientRect()
        section = self.find_anchor_section(rect)
        if section:
            self.anchor.row = section.lbo_row
            self.anchor.offset = section.getBoundingClientRect().top-rect.top-self.header.height
        else:
            self.anchor.row = int(scroll_top / self.row_height)
            self.anchor.offset = 0

        self.update_display()
        self._scroll_pending = False

    def find_anchor_section(self, rect):
        x = (rect.left + rect.right)/2
        y = (rect.top + rect.bottom)/2
        for el in document.elementsFromPoint(x, y):
            if el.tagName == "SECTION":
                return el

    def start_provider(self):
        value = self.context.value
        style = self.context.get("style")
        if isinstance(value, TableDataProvider):
            self.provider = value
        else:
            self.provider = adapter.get(type(value), TableDataProvider, style)

        self.header.start()
        self.footer.start()
        self.provider.set_table(self)


class TemplateBase:
    def __init__(self, template, contexts):
        self.template = template
        self.contexts = contexts


class FixedRenderer(Reactive):
    def __init__(self, template):
        self.template = template

    @rule
    def _rule_render_cells(self):
        contexts = self.template.contexts
        for i, el in enumerate(self.template.elements):
            contexts[i].renderer(el)
        self.template.height = self.template.elements[0].getBoundingClientRect().height


# __pragma__("jscall")
class RowTemplate(TemplateBase):
    SECTION = "b"
    TAG = "div"
    SECTION_TAG = "section"
    BACK = "body"

    def render(self, table, css_offset):
        row = table.render_context.row
        clone = self.template.content.cloneNode(True)
        for i, el in enumerate(clone.children):
            context = self.contexts[i]
            context.renderer(el)
            el.lbo_row = row
            el.lbo_col = i - 1
            el.style.gridRowStart = str(context.rows[0]+row+css_offset)
            el.style.gridRowEnd = str(context.rows[1]+row+css_offset+1)
            i += 1
        return clone


class HeaderTemplate(TemplateBase):
    SECTION = "h"
    TAG = "header"
    SECTION_TAG = "header"
    BACK = "header"

    def start(self):
        self.rule_renderer = FixedRenderer(self)

    def render_into_viewport(self, table):
        self.elements = []
        clone = self.template.content.cloneNode(True)
        for i, el in enumerate(clone.children):
            el.lbo_row = -1
            el.lbo_col = i - 1
            self.elements.append(el)

        back = clone.firstChild
        table.viewport.insertBefore(clone, table.viewport.firstChild)
        self.height = back.getBoundingClientRect().height

    def complete_template(self, viewport):
        """calculate the top positions for sticky headers"""
        children = self.template.content.children
        viewport.appendChild(self.template.content.cloneNode(True))
        top = viewport.getBoundingClientRect().top
        for i, el in enumerate(viewport.children):
            rect = el.getBoundingClientRect()
            children[i].style.top = (rect.top - top)+"px"
        self.row_count = max([c["rows"][1] for c in self.contexts]) + 1
        viewport.replaceChildren()


class FooterTemplate(TemplateBase):
    SECTION = "f"
    TAG = "footer"
    BACK = "footer"
    SECTION_TAG = "footer"

    def start(self):
        self.rule_renderer = FixedRenderer(self)

    def render_into_viewport(self, table):
        self.elements = []
        clone = self.template.content.cloneNode(True)
        for i, el in enumerate(clone.children):
            el.lbo_row = -2
            el.lbo_col = i - 1
            self.elements.append(el)

        back = clone.firstChild
        table.viewport.appendChild(clone)
        self.height = back.getBoundingClientRect().height

    def complete_template(self, viewport):
        """calculate the bottom positions for sticky footers"""
        viewport.appendChild(self.template.content.cloneNode(True))
        bottoms = []
        for i, el in enumerate(viewport.children):
            bottoms.append(el.getBoundingClientRect().bottom)
        self.height = viewport.firstChild.getBoundingClientRect().height
        viewport.replaceChildren()

        self.row_count = max([c["rows"][1] for c in self.contexts]) + 1

        max_bottom = max(bottoms)
        for i, c in enumerate(self.template.content.children):
            context = self.contexts[i]
            c.style.bottom = (max_bottom - bottoms[i])+"px"
            c.style.gridRowStart = context.rows[0] - self.row_count - 1
            c.style.gridRowEnd = context.rows[1] - self.row_count


class DumyTemplate:
    row_count = 0
    height = 0

    def render_into_viewport(self, table):
        return

    def start(self):
        pass

# __pragma__("nojscall")
