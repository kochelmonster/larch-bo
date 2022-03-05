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


TODO:
- force variable record heights
- page down/end
- chunked

"""

import larch.lib.adapter as adapter
from larch.reactive import rule, Cell, Reactive
from ..i18n import HTML
from ..control import Control
from ..browser import get_metrics
from ..js.debounce import debounce
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
    row_count = 0
    element = Cell()
    updated = Cell(0)
    control_handlers = {}

    def __init__(self, cv):
        super().__init__(cv)
        self.value_painters = {}  # __:jsiter
        self.render_context = {}  # __:jsiter
        self.anchor = {"row": 0, "offset": 0}  # __:jsiter
        """the first visible row with its distance from the viewports top"""

        self.max_block_size = 100
        """the maximum count of rows inside the display block"""

        self.block_size = 0
        """the count of filled rows of display block"""

        self.rows = []
        """the row elements of display block"""

        self.row_heights = {}
        """cache for row heights"""

        self.update_columns = debounce(self.update_columns, 100)

    def render(self, parent):
        self.context.control = self
        el = document.createElement("div")
        el.classList.add("lbo-table")

        self.viewport = document.createElement("div")
        el.appendChild(self.viewport)
        parent.appendChild(el)

        self.process_layout()

        self.header.complete_template(self.viewport)
        self.footer.complete_template(self.viewport)
        el.addEventListener("scroll", self.on_scroll)

        el.table = self   # debug
        self.element = el
        self.render_frame()
        self.reset_widths()
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

    def calc_max_block_size(self):
        # set max_block_size big enough to cover the screen
        # can be overwritten by sublasses
        return int(2 * window.screen.height / self.row_height)

    def set_row_count(self, count):
        self.row_count = count

        metrics = get_metrics()
        self.current_row_height = self.row_height = metrics.line_height

        if count > self.STATIC_LIMIT:
            self.max_block_size = self.calc_max_block_size()
        else:
            self.block_size = self.max_block_size = count  # still performant

        self.set_virtual_scroll_space(count)
        self.update_row_templates()
        self.update_rows()

        # we estimate the row height from the first rows
        display_height = sum([section.getBoundingClientRect().height for section in self.rows])
        self.current_row_height = self.row_height = display_height / self.block_size

        if count > self.STATIC_LIMIT:
            self.columns = window.getComputedStyle(self.viewport)["grid-template-columns"]
            # change block_size to a more suitable value
            self.max_block_size = self.calc_max_block_size()

        self.set_virtual_scroll_space(count)
        self.update_scrollbar(False)

    def set_virtual_scroll_space(self, count):
        self.virtual_scroll_space = min(self.row_height * count, 800000)
        self.row_height = self.virtual_scroll_space / count
        console.log("***virtual_scroll_space", self.virtual_scroll_space)

    def update_row_templates(self):
        upper_rows = (self.header.row_count   # header
                      + 1                     # upper scroll spanner
                      + self.max_block_size   # body
                      + 1)                    # lower scroll spanner
        rows = (f"repeat({upper_rows}, auto) 1fr repeat({self.footer.row_count}, auto)"
                if self.footer.row_count else f"repeat({upper_rows}, auto) 1fr")
        self.viewport.style["grid-template-rows"] = rows

        self.rows = []
        tmp = __new__(DocumentFragment())
        # delete complete body
        tmp.append.apply(tmp, self.viewport.querySelectorAll(".b"))
        tmp.replaceChildren()
        offset = (self.header.row_count + 1   # one based
                  + 1)                        # upper scroll spanner
        for i in range(offset, self.max_block_size+offset):
            el = self.body.render(i)
            self.rows.append(el.firstChild)
            tmp.append(el)
        self.viewport.insertBefore(tmp, self.lower_scroll)

    def update_data(self):
        self.fill_display_block()
        self.update_scrollbar(True)
        self.updated += 1

    def needs_update(self):
        if not self.block_size:
            return True

        start_row = self.rows[0]
        index = self.anchor.row - start_row.lbo_row
        if not 0 <= index < self.block_size:
            return True

        anchor = self.rows[index]
        erect = self.element.getBoundingClientRect()
        aoffset = anchor.getBoundingClientRect().top - erect.top - self.header.height
        delta = self.anchor.offset - aoffset
        # virtually move the viewport to the real self.anchor.offset

        top = self.upper_scroll.getBoundingClientRect().bottom + delta
        if erect.top + self.header.height < top:
            return True

        bottom = self.lower_scroll.getBoundingClientRect().top + delta
        if erect.bottom - self.footer.height > bottom:
            return True

        return False

    def update_rows(self):
        if self.needs_update():
            self.fill_display_block()
            if self.row_count > self.STATIC_LIMIT:
                self.update_columns()
            return True

    def update_columns(self):
        columns = window.getComputedStyle(self.viewport)["grid-template-columns"]
        if columns != self.columns:
            self.columns = columns
            columns = columns.split(" ")
            tmp = []
            for size, c in zip(columns, self.stretchers):
                tmp.append(f"{c.stretch}fr" if c.stretch else f"minmax({size}, auto)")
            self.viewport.style["grid-template-columns"] = " ".join(tmp)

    def update_display(self, keep_scroll_top=False):
        if self.update_rows():
            self.update_scrollbar(keep_scroll_top)
        self.updated += 1

    def update_scrollbar(self, keep_scroll_top=True):
        if keep_scroll_top:
            upper_space = scroll_top = self.element.scrollTop
            for i in range(self.block_size):
                row_no = self.rows[i].lbo_row
                if row_no >= self.anchor.row:
                    upper_space += self.anchor.offset
                    break
                upper_space -= self.row_heights[row_no]
        else:
            upper_space = scroll_top = self.row_height * self.rows[0].lbo_row
            for i in range(self.block_size):
                row_no = self.rows[i].lbo_row
                if row_no >= self.anchor.row:
                    scroll_top -= self.anchor.offset
                    break
                scroll_top += self.row_heights[row_no]

        start_row = self.rows[0].lbo_row
        if not start_row:
            upper_space = 0

        if start_row + self.block_size == self.row_count:
            vsp = self.virtual_scroll_space
            self.virtual_scroll_space = self.display_height + upper_space
            console.log("***set virtual_scroll_space", self.display_height, upper_space, self.virtual_scroll_space, vsp)

        self.element.scrollTop = 0  # bugfix for chrome
        lower_space = self.virtual_scroll_space - self.display_height - upper_space
        self.upper_scroll.style.height = upper_space + "px"
        self.lower_scroll.style.height = lower_space + "px"
        self.element.scrollTop = scroll_top

        console.log("***update scrollbar", [self.element.scrollTop, scroll_top],
                    [self.element.scrollHeight, self.virtual_scroll_space],
                    [self.display_height, upper_space, lower_space],
                    self.anchor.row, self.block_size)

    def get_display_range(self):
        if self.block_size:
            return [self.rows[0].lbo_row, self.rows[self.block_size-1].lbo_row]
        return [-1, -1]

    def fill_display_block(self):
        row_heights = {}
        start = max(self.anchor.row - 4, 0)
        end = min(start+self.max_block_size, self.row_count)
        start = min(start, end - 4)  # self.ancho
        data = self.provider.request(start, end)
        display_height = i = 0

        def render_row(i):
            row = self.rows[i]
            row_no = self.render_context.row = start + i
            self.render_context.value = data[i]
            self.body.render_content(row, row_no)
            height = self.row_heights[row_no] or row.getBoundingClientRect().height
            row_heights[row_no] = height
            return height

        # fill the first 4 rows (above display)
        while i < 4:
            display_height += render_row(i)
            i += 1

        # fill the display with enough rows
        top_offset = display_height
        rect = self.element.getBoundingClientRect()
        visible_height = rect.height - self.header.height - self.footer.height
        end = len(data)
        while display_height - top_offset < visible_height and i < end:
            display_height += render_row(i)
            i += 1

        # fill the next 4 rows (below display)
        end = min(i + 4, len(data))
        while i < end:
            display_height += render_row(i)
            i += 1

        self.block_size = i
        self.row_heights = row_heights
        self.display_height = display_height

        if display_height - top_offset < rect.height and start > 0:
            # display to small -> move anchor
            self.anchor.row = max(self.anchor.row-4, 0)
            self.anchor.offset -= top_offset
            self.fill_display_block()
            return

        # hide all non necessary rows
        el = self.rows[i]
        while el and el is not self.lower_scroll:
            el.style.display = "none"
            el = el.nextElementSibling

        if "__placeholder__" in data[0]:
            self.element.classList.add("placeholder")
        else:
            self.element.classList.remove("placeholder")

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
        rect = self.element.getBoundingClientRect()
        section = self.find_anchor_section(rect)
        console.log("**on_scroll", section)
        if section:
            self.anchor.row = section.lbo_row
            self.anchor.offset = section.getBoundingClientRect().top-rect.top-self.header.height
        else:
            self.anchor.row = min(int(self.element.scrollTop / self.row_height), self.row_count-1)
            self.anchor.offset = 0

        self.update_display(True)

    def update_anchor(self):
        rect = self.element.getBoundingClientRect()
        anchor = self.find_anchor_section(rect)
        if not anchor:
            anchor = self.rows[0]

        self.anchor.row = anchor.lbo_row
        self.anchor.offset = anchor.getBoundingClientRect().top-rect.top-self.header.height

    def find_anchor_section(self, rect):
        lower = self.upper_scroll.getBoundingClientRect().bottom
        visible_border = rect.top + self.header.height
        if lower < visible_border:
            bottom = lower
            for i in range(self.block_size):
                bottom += self.row_heights[self.rows[i].lbo_row]
                if bottom > visible_border:
                    return self.rows[i]

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

    def get_state(self):
        """"the tables state"""
        return {"anchor": self.anchor}  # __:jsiter

    def set_state(self, state):
        anchor = (state and state.anchor) or self.anchor
        self.anchor.row = anchor.row
        self.anchor.offset = anchor.offset


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

    def render(self, row):
        clone = self.template.content.cloneNode(True)
        i = 0
        for el in clone.children:
            context = self.contexts[i]
            el.lbo_row = row
            el.lbo_col = i - 1
            el.style.gridRowStart = str(context.rows[0]+row)
            el.style.gridRowEnd = str(context.rows[1]+row+1)
            i += 1
        return clone

    def render_content(self, element, row):
        for c in self.contexts:
            element.lbo_row = row
            element.style.display = ""
            c.renderer(element)
            element = element.nextElementSibling


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
