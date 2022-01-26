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
__new__ = DocumentFragment = console = document = window = None
def require(n): pass
def __pragma__(**args): pass
# __pragma__ ("noskip")


require("./larch.bo.table.scss")


class Table(Control):
    STATIC_LIMIT = 200   # below this row_count no virtual list
    TOLERANCE = 7        # for better berformance
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

        self.block_size = 1
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
        area.classList.add("back", factory.SECTION)
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

    def clear(self):
        tmp = __new__(DocumentFragment())
        tmp.append.apply(tmp, self.viewport.querySelectorAll(".b"))
        self.row_start = self.row_end = self.row_count = 0
        self.upper_scroll.style.height = "0"
        self.lower_scroll.style.height = "0"
        self.anchor.row = 0
        self.anchor.offset = 0

    def set_row_count(self, count):
        if count < self.STATIC_LIMIT:
            self.row_count = count
            self.block_size = count  # still performant
            self.update_row_templates()
            self.virtual_mode = False
            self.update_display()
            self.element.removeEventListener("scroll", self.on_scroll)
            return

        update_block_size = False
        if self.row_count < self.STATIC_LIMIT:
            metrics = get_metrics()
            self.block_size = int(2 * window.screen.height / metrics.line_height)
            # enough to cover the screen
            update_block_size = True
            self.virtual_mode = False
            self.update_row_templates()
            self.update_display()
            self.element.addEventListener("scroll", self.on_scroll)
            self.columns = window.getComputedStyle(self.viewport)["grid-template-columns"]

        elif self.row_end > count - 1:
            # shorten the display
            self.set_virtual_scroll_space(count)
            self.update_display()
        else:
            self.set_virtual_scroll_space(count)

        self.row_count = count
        self.virtual_mode = True

        if update_block_size:
            # we estimate the row height from the first rows
            display_height = sum([section.getBoundingClientRect().height for section in self.rows])
            self.row_height = display_height / (self.row_end - self.row_start)

            # change block_size to a more suitable value
            self.block_size = int(2.5 * window.screen.height / self.row_height)
            self.set_virtual_scroll_space(count)
            self.update_row_templates()
            self.update_display()

    def set_virtual_scroll_space(self, count):
        # self.virtual_scroll_space = min(self.row_height * count, 33000000)
        self.virtual_scroll_space = min(self.row_height * count, 800000)
        self.row_height = self.virtual_scroll_space / count

    def update_row_templates(self):
        upper_rows = (self.header.row_count   # header
                      + 1                     # upper scroll spanner
                      + self.block_size       # body
                      + 1)                    # lower scroll spanner
        rows = (f"repeat({upper_rows}, auto) 1fr repeat({self.footer.row_count}, auto)"
                if self.footer.row_count else f"repeat({upper_rows}, auto) 1fr")
        self.viewport.style["grid-template-rows"] = rows

    def update_data(self):
        tmp = __new__(DocumentFragment())
        # delete complete display_block
        tmp.append.apply(tmp, self.viewport.querySelectorAll(".b"))
        tmp.replaceChildren()

        # insert_new display_bloc
        self.fill_display_block(tmp)
        self.viewport.insertBefore(tmp, self.lower_scroll)

        if self.virtual_mode:
            self.update_scrollbar()

        self.update_anchor()
        self.updated += 1

    def needs_display_update(self):
        upper_row = self.upper_scroll.nextSibling.lbo_row
        if upper_row < 0:
            return True

        if self.row_start <= 0 or self.row_end >= self.row_count - 1:
            return True

        tolerance = self.TOLERANCE
        if self.row_start - tolerance < upper_row < self.row_start + tolerance:
            lower_row = self.lower_scroll.previousSibling.lbo_row
            if self.row_end - tolerance < lower_row < self.row_end + tolerance:
                return False

        return True

    def update_display(self):
        self.row_start = max(self.anchor.row - self.block_size//2, 0)
        self.row_end = min(self.row_start + self.block_size, self.row_count)
        self.row_start = max(self.row_end - self.block_size, 0)

        if self.needs_display_update():
            tmp = __new__(DocumentFragment())
            tmp.append.apply(tmp, self.viewport.querySelectorAll(".b"))
            el = tmp.firstElementChild
            while el:
                next = el.nextElementSibling
                if not self.row_start <= el.lbo_row < self.row_end:
                    el.remove()
                el = next

            self.fill_display_block(tmp)
            self.viewport.insertBefore(tmp, self.lower_scroll)

            if self.virtual_mode:
                columns = window.getComputedStyle(self.viewport)["grid-template-columns"]
                if columns != self.columns:
                    self.columns = columns
                    columns = columns.split(" ")
                    tmp = []
                    for size, c in zip(columns, self.stretchers):
                        tmp.append(f"{c.stretch}fr" if c.stretch else f"minmax({size}, auto)")
                    self.viewport.style["grid-template-columns"] = " ".join(tmp)

        if self.virtual_mode:
            self.update_scrollbar()

        self.update_anchor()
        self.updated += 1

    def update_scrollbar(self):
        real_height = sum([section.getBoundingClientRect().height for section in self.rows])
        virtual_height = self.row_height * self.rows.length
        delta = virtual_height - real_height

        element_rect = self.element.getBoundingClientRect()
        top_section = self.rows[0]
        row_start = top_section.lbo_row
        anchor = self.rows[self.anchor.row - row_start]

        # inside the display block
        scroll_pos = (anchor.getBoundingClientRect().top
                      - top_section.getBoundingClientRect().top
                      - self.anchor.offset)
        if self.row_end == self.row_count:
            real_height -= element_rect.height

        relation = scroll_pos / real_height
        relation = max(0, min(1, relation))

        row_end = self.rows[self.rows.length-1].lbo_row + 1
        upper_space = row_start * self.row_height + delta * relation
        lower_space = (self.row_count - row_end) * self.row_height + delta * (1-relation)

        self.upper_scroll.style.height = upper_space + "px"
        self.lower_scroll.style.height = lower_space + "px"

        # scroll the anchor to the correct position
        aoffset = anchor.getBoundingClientRect().top - element_rect.top - self.header.height
        delta_scroll = int(aoffset - self.anchor.offset)
        if delta_scroll:
            self.element.removeEventListener("scroll", self.on_scroll)
            self.element.scrollTop += delta_scroll
            self.element.addEventListener("scroll", self.on_scroll)

    def update_anchor(self):
        rect = self.element.getBoundingClientRect()
        anchor = self.find_anchor_section(rect)
        if not anchor:
            anchor = self.rows[0]

        self.anchor.row = anchor.lbo_row
        self.anchor.offset = anchor.getBoundingClientRect().top-rect.top-self.header.height

    def fill_display_block(self, tmp):
        first = tmp.firstElementChild
        has_placeholder = False
        if first and self.row_start < first.lbo_row:
            data = self.provider.request(self.row_start, first.lbo_row)
            has_placeholder = "__placeholder__" in data[0]
            row = self.row_start
            nodes = []
            for val in data:
                self.render_context.row = row
                self.render_context.value = val
                nodes.append(self.body.render(self))
                row += 1
            tmp.prepend.apply(tmp, nodes)

        last = tmp.lastElementChild
        row = self.row_start if not last else last.lbo_row+1
        if row < self.row_end:
            data = self.provider.request(row, self.row_end)
            has_placeholder = has_placeholder or "__placeholder__" in data[0]
            for val in data:
                self.render_context.row = row
                self.render_context.value = val
                tmp.append(self.body.render(self))
                row += 1

        if has_placeholder:
            self.element.classList.add("placeholder")
        else:
            self.element.classList.remove("placeholder")

        css_row = (self.header.row_count + 1   # one based
                   + 1)                        # upper scroll spanner
        self.rows = tmp.querySelectorAll("section")
        for r in self.rows:
            self.body.reposition(r, css_row)
            css_row += 1

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
        rect = self.element.getBoundingClientRect()
        section = self.find_anchor_section(rect)
        if section:
            self.anchor.row = section.lbo_row
            self.anchor.offset = section.getBoundingClientRect().top-rect.top-self.header.height
        else:
            self.anchor.row = min(int(self.element.scrollTop / self.row_height), self.row_count-1)
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
            provider = value
        else:
            provider = adapter.get(type(value), TableDataProvider, style)

        provider.set_table(self)
        self.header.start()
        self.footer.start()


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
        i = 0
        for el in clone.children:
            context = self.contexts[i]
            context.renderer(el)
            el.lbo_row = row
            el.lbo_col = i - 1
            el.style.gridRowStart = str(context.rows[0]+row+css_offset)
            el.style.gridRowEnd = str(context.rows[1]+row+css_offset+1)
            i += 1
        return clone

    def reposition(self, element, css_row):
        for c in self.contexts:
            element.style.gridRowStart = str(c.rows[0]+css_row)
            element.style.gridRowEnd = str(c.rows[1]+css_row+1)
            element = element.nextSibling


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

    def start(self):
        pass

    def render_into_viewport(self, table):
        pass

    def complete_template(self, viewport):
        pass

# __pragma__("nojscall")
