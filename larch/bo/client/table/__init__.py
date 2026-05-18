"""
A virtual tree table based on css grid.

The vertical Layout of the grid:
+---------------------------------------+
| header (sticky, optional)             |
+---------------------------------------+
| body                                  | <-- display block
+---------------------------------------+
| empty  (1fr)                          |
+---------------------------------------+
| footer (sticky, optional)             |
+---------------------------------------+

The empty row is responsible for pushing the footer to the bottom of the
containing cell when the table is vertically stretched.
"""

import larch.lib.adapter as adapter
from larch.reactive import rule, Cell, Reactive
from ..i18n import HTML
from ..control import Control, ControlContext
from ..browser import get_metrics
from ..animate import animator
from ..js.debounce import debounce
from .parser import TableParser
from .provider import TableDataProvider


# __pragma__("skip")
__new__ = DocumentFragment = console = document = window = Date = None
def require(n): pass
def __pragma__(**args): pass
# __pragma__ ("noskip")


require("./larch.bo.table.scss")


DEBUG = False
"""Set to True to enable [table] diagnostic logging."""


def _log(msg):
    if DEBUG:
        console.log(msg)


class VirtualHandler:
    """
    Mixin to handle the virtual table mechanism.

    Virtual mode: anchor row = first visible row = first body grid position.
    Renders visible_count + buffer_below rows. Buffer extends below viewport
    (clipped by overflow:hidden). No buffer above (CSS grid align-content:start
    would make rows above anchor visible).

    Scroll classification:
    - Near scroll: |delta| <= max_block_size/2 - incremental row recycling
    - Far scroll: larger jump - full rebuild from pool
    """
    VIRTUAL_SCROLL_MAX_PX = 800000
    """Cap on virtual_scroll_space - empirical browser-friendly upper bound
    before fractional pixel mapping gets clipped by some engines."""

    SCROLL_TOOLTIP_HIDE_MS = 800
    SCROLL_TOOLTIP_HEIGHT = 24
    END_ALIGN_EPSILON_PX = 2

    scroll_row = Cell(0)

    def __init__(self, cv):
        super().__init__(cv)

        self.anchor = {"row": 0, "bottom": None}  # __:jsiter
        """anchor.row = first visible row (top mode) or bottom-aligned row
        (bottom mode).  anchor.bottom = None means top-aligned;
        anchor.bottom = <px> means the row's bottom is <px> above viewport
        bottom (0 = flush)."""

        self.first_row = 0
        """data index of self.rows[0]"""

        self.visible_count = 0
        """number of rows fitting in viewport"""

        self.buffer_below = 0
        """extra rows rendered below visible area"""

        self._scroll_pending = False
        self._fill_scheduled = False
        self._expected_scroll_top = None
        """for scroll suppression: expected scrollTop after programmatic changes"""

        self._scroll_tooltip_timer = None
        self.scroll_tooltip = None
        self.scroll_tooltip_control = None
        self._resize_observer = None
        self._on_scroll_listener = None
        self._on_wheel_listener = None

    def _init_scroll_tooltip_control(self):
        self.scroll_tooltip_control = None
        if self.scroll_tooltip is None:
            return

        factory = adapter.get(type(self), Control, "scrolltip")
        if not factory:
            self.scroll_tooltip.style.display = "none"
            return

        context = ControlContext(self, self.context, style="scrolltip")
        self.scroll_tooltip.style.display = ""
        self.scroll_tooltip.replaceChildren()
        self.scroll_tooltip_control = factory(context)
        self.scroll_tooltip_control.render(self.scroll_tooltip)

    # --- Scroll event handling ---

    def on_scroll(self):
        if not self.is_virtual():
            return

        self._show_scroll_tooltip()

        if self._scroll_pending:
            return

        self._scroll_pending = True
        window.requestAnimationFrame(self._handle_scroll)

    def _on_wheel(self, event):
        if not self.is_virtual():
            return
        delta = event.deltaY
        if not delta:
            return
        # only consume the wheel when the scrollbar can still move in that
        # direction - otherwise let it bubble for ancestor scrolling
        max_scroll = (self.scrollbar_container.scrollHeight
                      - self.scrollbar_container.clientHeight)
        scroll_top = self.scrollbar_container.scrollTop
        if delta < 0 and scroll_top <= 0:
            return
        if delta > 0 and scroll_top >= max_scroll:
            return
        event.preventDefault()
        self.scrollbar_container.scrollBy(0, delta)

    def _handle_scroll(self):
        self._scroll_pending = False

        # suppress programmatic scroll events
        scroll_top = self.scrollbar_container.scrollTop
        if (self._expected_scroll_top is not None
                and abs(scroll_top - self._expected_scroll_top) < 1):
            self._expected_scroll_top = None
            return

        if not self.row_height or not self.row_count:
            return

        max_scroll = (self.scrollbar_container.scrollHeight
                      - self.scrollbar_container.clientHeight)
        if max_scroll > 0 and max_scroll - scroll_top <= self.END_ALIGN_EPSILON_PX:
            end_row = max(0, self.row_count - 1)
            if self.anchor.row != end_row or self.anchor.bottom is None:
                self.anchor.row = end_row
                self.anchor.bottom = 0
                _log(f"[table] _handle_scroll: end-align row={end_row}")
                self.fill_virtual_body()
            return

        new_anchor = self._scrolltop_to_anchor(scroll_top)
        if new_anchor == self.first_row:
            if self.anchor.bottom is not None:
                self.anchor.bottom = None
                self._apply_anchor_offset()
            return

        self.anchor.bottom = None
        delta = abs(new_anchor - self.first_row)
        threshold = self.max_block_size / 2
        if delta > threshold:
            _log(f"[table] _handle_scroll: anchor={new_anchor} first_row={self.first_row} delta={delta} mode=far")
            self._scroll_far(new_anchor)
        else:
            _log(f"[table] _handle_scroll: anchor={new_anchor} first_row={self.first_row} delta={delta} mode=near")
            self._scroll_near(new_anchor)

    def _scrolltop_to_anchor(self, scroll_top):
        if not self.virtual_scroll_space:
            return 0
        max_scroll = (self.scrollbar_container.scrollHeight
                      - self.scrollbar_container.clientHeight)
        if max_scroll <= 0:
            return 0
        max_anchor = self.row_count - self.visible_count
        if max_anchor <= 0:
            return 0
        if max_scroll - scroll_top <= self.END_ALIGN_EPSILON_PX:
            return max_anchor
        row = int((scroll_top / max_scroll) * max_anchor)
        return max(0, min(row, max_anchor))

    def _sync_scrollbar(self):
        if not self.row_count:
            return
        max_scroll = (self.scrollbar_container.scrollHeight
                      - self.scrollbar_container.clientHeight)
        max_anchor = self.row_count - self.visible_count
        if max_scroll <= 0 or max_anchor <= 0:
            return
        expected = (self.first_row / max_anchor) * max_scroll
        current = self.scrollbar_container.scrollTop
        if abs(expected - current) > 1:
            self._expected_scroll_top = expected
            self.scrollbar_container.scrollTop = expected
        self._show_scroll_tooltip()

    def _show_scroll_tooltip(self):
        if not self.scroll_tooltip_control or not self.row_count:
            return
        max_scroll = (self.scrollbar_container.scrollHeight
                      - self.scrollbar_container.clientHeight)
        if max_scroll <= 0:
            return
        scroll_top = self.scrollbar_container.scrollTop

        self.scroll_row = self._scrolltop_to_anchor(scroll_top)

        # position vertically to match thumb
        area_height = self.scrollbar_container.clientHeight
        ratio = scroll_top / max_scroll
        top = ratio * (area_height - self.SCROLL_TOOLTIP_HEIGHT)
        self.scroll_tooltip.style.top = f"{top}px"
        animator.show(self.scroll_tooltip, True)

        if self._scroll_tooltip_timer:
            window.clearTimeout(self._scroll_tooltip_timer)
        self._scroll_tooltip_timer = window.setTimeout(
            self._hide_scroll_tooltip, self.SCROLL_TOOLTIP_HIDE_MS)

    def _hide_scroll_tooltip(self):
        self._scroll_tooltip_timer = None
        if self.scroll_tooltip:
            animator.show(self.scroll_tooltip, False)

    def _apply_anchor_offset(self):
        """Apply pixel-accurate viewport offset for sub-row positioning."""
        self.element.scrollTop = 0
        if self.anchor.bottom is not None:
            # Use CSS grid alignment to push rows to bottom when needed
            self.viewport.style.alignContent = "flex-end"
            self._apply_bottom_alignment()
        else:
            # Normal top-aligned rendering
            self.viewport.style.alignContent = "start"

    def _apply_bottom_alignment(self):
        """Position anchor.row's bottom flush with viewport bottom."""
        if self.anchor.bottom is None or not len(self.rows):
            return
        start = self.rows[0].lbo_row
        idx = self.anchor.row - start
        if idx < 0 or idx >= len(self.rows):
            _log(f"[table] _apply_bottom_alignment: SKIP anchor.row={self.anchor.row} start={start} idx={idx} rows={len(self.rows)}")
            return
        self.element.scrollTop = 0
        row = self.rows[idx]
        # measure relative to viewport (where the rows live), not the outer
        # element, so border/padding on .lbo-table does not skew the offset
        view_rect = self.viewport.getBoundingClientRect()
        max_bottom = view_rect.bottom - self.footer.height
        row_rect = row.getBoundingClientRect()
        needed = row_rect.bottom - max_bottom + self.anchor.bottom
        if needed > 0.5:
            self.element.scrollTop = needed

    # --- Near scroll (incremental) ---

    def _scroll_near(self, new_anchor):
        self._fill_scheduled = False
        new_anchor = max(0, min(new_anchor, self.row_count - 1))
        delta = new_anchor - self.first_row
        if delta == 0:
            self._apply_anchor_offset()
            return

        self.anchor.bottom = None
        target_count = min(
            self.visible_count + self.buffer_below + 1,
            self.row_count - new_anchor)

        if delta > 0:
            # scroll down: remove rows from front, add at end
            remove_count = min(delta, len(self.rows))
            for i in range(remove_count):
                row_el = self.rows[0]
                fragment = self.body.move(row_el)
                self.row_pool.append(fragment)
                self.rows.pop(0)

            # add new rows at end
            old_last = self.first_row + delta + len(self.rows)
            need = target_count - len(self.rows)
            if need > 0:
                end_row = min(old_last + need, self.row_count)
                if end_row > old_last:
                    data = self.provider.request_data(old_last, end_row)
                    for i, record in enumerate(data):
                        self.render_rows(old_last + i, len(self.rows), record)

        else:
            # scroll up: remove rows from end, add at front
            remove_count = min(-delta, len(self.rows))
            for i in range(remove_count):
                row_el = self.rows[len(self.rows) - 1]
                fragment = self.body.move(row_el)
                self.row_pool.append(fragment)
                self.rows.pop()

            # add new rows at front
            need = target_count - len(self.rows)
            if need > 0:
                start_row = new_anchor
                end_row = min(start_row + need, self.first_row)
                if end_row > start_row:
                    data = self.provider.request_data(start_row, end_row)
                    for i in range(len(data) - 1, -1, -1):
                        self.render_rows(start_row + i, -1, data[i])

        # trim excess rows from end
        while len(self.rows) > target_count:
            row_el = self.rows[len(self.rows) - 1]
            fragment = self.body.move(row_el)
            self.row_pool.append(fragment)
            self.rows.pop()

        self.first_row = new_anchor
        self.anchor.row = new_anchor

        # correct grid positions for all rows
        for grid_row, row_element in enumerate(
                self.rows, self.header.row_count + 1):
            self.body.correct_grid_row(row_element, grid_row)

        self._trim_pool()
        self._update_avg_height()
        self._update_columns_debounced()
        self._apply_anchor_offset()
        self.updated += 1

    # --- Far scroll (full rebuild) ---

    def _scroll_far(self, new_anchor):
        new_anchor = max(0, min(new_anchor, self.row_count - 1))
        self._clear_body_to_pool()
        self.anchor.row = new_anchor
        self.anchor.bottom = None
        self.fill_virtual_body()

    # --- Body fill ---

    def _deferred_fill(self):
        """Schedule fill_virtual_body on next animation frame.
        Coalesces rapid calls — only the last anchor state is used."""
        if self._fill_scheduled:
            return
        self._fill_scheduled = True
        window.requestAnimationFrame(self._execute_deferred_fill)

    def _execute_deferred_fill(self):
        if not self._fill_scheduled:
            return
        self._fill_scheduled = False
        self.fill_virtual_body()

    def fill_virtual_body(self):
        self._fill_scheduled = False
        self._clear_body_to_pool()

        # clamp anchor.row defensively
        max_anchor = max(0, self.row_count - 1)
        if self.anchor.row > max_anchor:
            self.anchor.row = max_anchor

        if self.anchor.bottom is not None:
            # bottom mode: anchor.row is the row to align at bottom
            self.first_row = max(0, self.anchor.row - self.visible_count)
        else:
            self.first_row = self.anchor.row

        # clamp first_row to a valid range so target_count is never negative
        if self.first_row > max_anchor:
            self.first_row = max(0, max_anchor)

        target_count = min(
            self.visible_count + self.buffer_below + 1,
            self.row_count - self.first_row)

        _log(f"[table] fill_virtual_body: anchor.row={self.anchor.row} anchor.bottom={self.anchor.bottom} first_row={self.first_row} target={target_count}")

        if target_count <= 0:
            self.updated += 1
            return

        data_start = self.first_row
        data_end = min(data_start + target_count, self.row_count)
        data = self.provider.request_data(data_start, data_end)

        for i, record in enumerate(data):
            self.render_rows(data_start + i, len(self.rows), record)

        # correct grid positions for all rows
        for grid_row, row_element in enumerate(
                self.rows, self.header.row_count + 1):
            self.body.correct_grid_row(row_element, grid_row)

        self._update_avg_height()
        self._update_columns_debounced()
        self._apply_anchor_offset()
        self.updated += 1

    def fill_static_body(self):
        self._clear_body_to_pool()

        data = self.provider.request_data(0, self.row_count)

        self.row_heights = {}  # __:jsiter
        for i, record in enumerate(data):
            self.row_heights[i] = self.render_rows(i, i, record)

        for grid_row, row_element in enumerate(
                self.rows, self.header.row_count + 1):
            self.body.correct_grid_row(row_element, grid_row)

        self.updated += 1

    # --- Pool management ---

    def _clear_body_to_pool(self):
        """Move all body rows to pool for reuse."""
        for row_el in self.rows:
            fragment = self.body.move(row_el)
            self.row_pool.append(fragment)
        self.rows = []
        self._trim_pool()

    def _trim_pool(self):
        if len(self.row_pool) > self.max_block_size:
            self.row_pool = self.row_pool[-self.max_block_size:]

    def make_row(self):
        return self.row_pool.pop() if len(self.row_pool) else self.body.render(0)

    # --- Height tracking ---

    def _update_avg_height(self):
        count = 0
        total = 0
        # __pragma__("jsiter")
        for k in self.row_heights:
            total += self.row_heights[k]
            count += 1
        # __pragma__("nojsiter")
        if count > 0:
            self.row_height = total / count

    def _set_virtual_scroll_space(self):
        if not self.row_count:
            return

        measured_count = 0
        measured_total = 0
        # __pragma__("jsiter")
        for k in self.row_heights:
            measured_total += self.row_heights[k]
            measured_count += 1
        # __pragma__("nojsiter")

        if measured_count > 0:
            unmeasured = self.row_count - measured_count
            total = measured_total + unmeasured * self.row_height
        else:
            total = self.row_count * self.row_height

        self.virtual_scroll_space = min(total, self.VIRTUAL_SCROLL_MAX_PX)
        self.scroll_row_height = self.virtual_scroll_space / self.row_count
        self.scrollbar_spacer.style.height = f"{self.virtual_scroll_space}px"

    # --- Rendering ---

    def render(self, parent):
        # Main container
        container = document.createElement("div")
        container.classList.add("lbo-table-container")
        container.style.display = "flex"
        container.style.height = "100%"

        el = document.createElement("div")
        el.classList.add("lbo-table")
        self.viewport = document.createElement("div")
        el.appendChild(self.viewport)

        # Decoupled scrollbar
        self.scrollbar_container = document.createElement("div")
        self.scrollbar_container.classList.add("lbo-scrollbar-area")

        self.scrollbar_spacer = document.createElement("div")
        self.scrollbar_spacer.style.height = "0px"
        self.scrollbar_container.appendChild(self.scrollbar_spacer)

        # Scroll position tooltip
        self.scroll_tooltip = document.createElement("div")
        self.scroll_tooltip.classList.add("lbo-scroll-tooltip", "popup")

        container.appendChild(el)
        container.appendChild(self.scroll_tooltip)
        container.appendChild(self.scrollbar_container)
        parent.appendChild(container)
        self._init_scroll_tooltip_control()

        self._on_scroll_listener = self.on_scroll
        self.scrollbar_container.addEventListener(
            "scroll", self._on_scroll_listener)
        self._on_wheel_listener = self._on_wheel
        # __pragma__("jsiter")
        el.addEventListener("wheel", self._on_wheel_listener, {"passive": False})
        # __pragma__("nojsiter")

        self.process_layout(self.viewport)

        el.table = self
        self.element = el
        self.render_frame()
        self.reset_widths()
        self.header.start()
        self.footer.start()
        self.start_provider()

        # resize observer
        def on_resize(entries):
            self._on_resize()
        self._resize_observer = __new__(window.ResizeObserver(on_resize))
        self._resize_observer.observe(el)

    def reset_widths(self):
        self.viewport.style["grid-template-columns"] = " ".join(
            [f"{c.stretch}fr" if c.stretch else "auto" for c in self.stretchers])

    def render_frame(self):
        viewport = self.viewport
        viewport.replaceChildren()

        upper_rows = (self.header.row_count   # header
                      + 1)                    # body

        viewport.style["grid-template-rows"] = (
            f"repeat({upper_rows}, auto) 1fr repeat({self.footer.row_count}, auto)")

        self.header.render_into_viewport(self)
        self.footer.render_into_viewport(self)

    def clear(self):
        self._clear_body_to_pool()
        self.row_count = 0
        self.first_row = 0
        self.anchor.row = 0
        self.anchor.bottom = None
        self.row_heights = {}  # __:jsiter
        self._scroll_pending = False
        self._fill_scheduled = False
        self._expected_scroll_top = None
        self.columns = None
        self.virtual_scroll_space = 0
        self.scrollbar_spacer.style.height = "0px"

    def set_row_count(self, count):
        old_count = self.row_count
        self.row_count = count

        # clamp anchor to valid range
        if self.anchor.row >= count:
            old_anchor = self.anchor.row
            self.anchor.row = max(0, count - 1)
            self.anchor.bottom = 0
            _log(f"[table] set_row_count: anchor clamped {old_anchor}->{self.anchor.row}")

        if not self.row_height:
            metrics = get_metrics()
            self.row_height = metrics.line_height

        is_virtual = self.is_virtual()
        _log(f"[table] set_row_count({count}) old={old_count} virtual={is_virtual} row_height={self.row_height}")

        if is_virtual:
            rect = self.element.getBoundingClientRect()
            viewport_height = (rect.height - self.header.height
                               - self.footer.height)
            self.visible_count = max(1, int(viewport_height / self.row_height))
            self.buffer_below = self.visible_count
            self.max_block_size = self.visible_count + self.buffer_below + 1
            self.fill_body = self._deferred_fill
            self.element.style.overflowY = "hidden"
            self.scrollbar_container.style.display = ""
        else:
            self.fill_body = self.fill_static_body
            self.max_block_size = max(count, 1)
            self.anchor.row = 0
            self.element.style.overflowY = "auto"
            self.scrollbar_container.style.display = "none"

        self._set_virtual_scroll_space()
        self.row_heights = {}  # __:jsiter

        self.update_row_templates()
        if is_virtual:
            self.fill_virtual_body()
        else:
            self.fill_body()

        # re-estimate after rendering
        self._update_avg_height()

        if is_virtual:
            # Lock column widths to measured pixel values so subsequent renders
            # (placeholders -> real data) don't shift columns. We re-measure
            # from the current DOM every time, so CSS changes are picked up.
            self.columns = window.getComputedStyle(
                self.viewport)["grid-template-columns"]
            self.viewport.style["grid-template-columns"] = self.columns

            # recalc block size with measured row heights
            old_max = self.max_block_size
            self.visible_count = max(1, int(viewport_height / self.row_height))
            self.buffer_below = self.visible_count
            self.max_block_size = self.visible_count + self.buffer_below + 1
            if self.max_block_size != old_max:
                _log(f"[table] set_row_count: post-render recalc max_block {old_max}->{self.max_block_size}")
                self.update_row_templates()
                self.fill_virtual_body()

        self._set_virtual_scroll_space()

    def update_row_templates(self):
        upper_rows = (self.header.row_count   # header
                      + self.max_block_size)  # body

        rows = (f"repeat({upper_rows}, auto) 1fr repeat({self.footer.row_count}, auto)"
                if self.footer.row_count else f"repeat({upper_rows}, auto) 1fr")
        self.viewport.style["grid-template-rows"] = rows

    def redraw(self):
        """Redraw the body. Called by providers when the data set changes
        (e.g. expansion, sort)."""
        self.fill_body()

    def _update_columns(self):
        columns = window.getComputedStyle(
            self.viewport)["grid-template-columns"]
        if columns != self.columns:
            self.columns = columns
            self.viewport.style["grid-template-columns"] = columns

    def _on_resize(self):
        if not self.is_virtual() or not self.row_height:
            return

        self.anchor.bottom = None
        rect = self.element.getBoundingClientRect()
        viewport_height = rect.height - self.header.height - self.footer.height
        new_visible = max(1, int(viewport_height / self.row_height))

        if abs(new_visible - self.visible_count) >= 2:
            _log(f"[table] _on_resize: visible_count {self.visible_count}->{new_visible}")
            self.visible_count = new_visible
            self.buffer_below = new_visible
            new_max = new_visible + self.buffer_below + 1
            if new_max > self.max_block_size:
                self.max_block_size = new_max
                self.update_row_templates()
            else:
                self.max_block_size = new_max
            self.reset_widths()
            self.fill_virtual_body()
            self.columns = window.getComputedStyle(
                self.viewport)["grid-template-columns"]
            self.viewport.style["grid-template-columns"] = self.columns
            self._set_virtual_scroll_space()
            self._sync_scrollbar()


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
        self.template.height = self.template.elements[0].getBoundingClientRect(
        ).height


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
            el.style.gridRow = f"{context.rows[0]+row}/{context.rows[1]+row+1}"
            i += 1
        return clone

    def render_content(self, element, row):
        for c in self.contexts:
            element.lbo_row = row
            element.style.display = ""
            c.renderer(element)
            element = element.nextElementSibling

    def correct_grid_row(self, element, row):
        """correct the position of the element in the grid"""
        for c in self.contexts:
            # single style write per cell; avoids two synchronous style mutations
            element.style.gridRow = f"{c.rows[0]+row}/{c.rows[1]+row+1}"
            element = element.nextElementSibling

    def move(self, element):
        tmp = __new__(DocumentFragment())
        for c in self.contexts:
            last = element
            element = element.nextElementSibling
            tmp.append(last)
        return tmp


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
    """No-op template used when the layout has no header / body / footer.
    All methods are safe to call and produce no DOM mutations."""
    row_count = 0
    height = 0
    contexts = []

    def start(self):
        pass

    def render(self, row):
        return __new__(DocumentFragment())

    def render_content(self, element, row):
        pass

    def correct_grid_row(self, element, row):
        pass

    def move(self, element):
        return __new__(DocumentFragment())

    def render_into_viewport(self, table):
        pass

    def complete_template(self, viewport):
        pass

# __pragma__("nojscall")


class LayoutHandler:
    """
    Mixin to handle the layout of the table
    """

    layout = ""
    """the layout of the table as a string"""

    def process_layout(self, viewport):
        parser = TableParser(self.layout)
        self.stretchers = parser.column_stretchers
        self.header = self.create_row_template(parser.header, HeaderTemplate)
        self.body = self.create_row_template(parser.body, RowTemplate)
        self.footer = self.create_row_template(parser.footer, FooterTemplate)
        self.header.complete_template(viewport)
        self.footer.complete_template(viewport)

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


class Table(VirtualHandler, LayoutHandler, Control):
    STATIC_LIMIT = 200   # below this row_count no virtual list
    row_count = 0
    element = Cell()
    updated = Cell(0)
    control_handlers = {}

    def __init__(self, cv):
        super().__init__(cv)

        self.value_painters = {}  # __:jsiter
        """painter cache keyed by f"{name}|{type_name}" to invalidate when
        the cell value type changes for the same column."""
        self.render_context = {}  # __:jsiter

        self.max_block_size = 100
        self.row_heights = {}  # __:jsiter
        """cache for row heights"""

        self.row_height = 24
        """the average row height (default estimate)"""

        self.scroll_row_height = 24
        """virtual_scroll_space / row_count, for scroll mapping only"""

        self.rows = []
        """the row elements of display block"""

        self.row_pool = []
        """a pool of row elements to reuse"""

        self.provider = None
        self.columns = None
        self.virtual_scroll_space = 0

        self.fill_body = self.fill_static_body
        """default fill method, overridden in set_row_count"""

        self._update_columns_debounced = debounce(self._update_columns, 100)

    def is_virtual(self):
        return self.row_count > self.STATIC_LIMIT

    def get_display_range(self):
        """Return [first_row, last_row+1] of currently rendered rows"""
        if not len(self.rows):
            return [0, 0]
        return [self.rows[0].lbo_row,
                self.rows[len(self.rows)-1].lbo_row + 1]

    def render_rows(self, data_row, table_row, data):
        # table_row is the index inside self.rows (-1 = insert at front)
        row_element = None
        if table_row < 0:
            clone = self.make_row()
            row_element = clone.firstChild
            self.rows.insert(0, row_element)
            self.viewport.appendChild(clone)
        elif table_row >= len(self.rows):
            clone = self.make_row()
            row_element = clone.firstChild
            self.rows.append(row_element)
            self.viewport.appendChild(clone)
        else:
            row_element = self.rows[table_row]

        self.render_context.row = data_row
        self.render_context.value = data
        self.body.render_content(row_element, data_row)

        is_placeholder = bool(
            data and getattr(data, "__placeholder__", False))
        el = row_element
        # iterate exactly len(self.body.contexts) cells - this is the fixed
        # number of elements a row template produces
        for i in range(len(self.body.contexts)):
            if not el:
                break
            if is_placeholder:
                el.classList.add("placeholder")
            else:
                el.classList.remove("placeholder")
            el = el.nextElementSibling

        height = row_element.getBoundingClientRect().height
        self.row_heights[data_row] = height
        return height

    def refresh_visible_data(self):
        """Re-render content of all visible rows without pool cycling."""
        if not len(self.rows):
            return

        first = self.rows[0].lbo_row
        last = self.rows[len(self.rows) - 1].lbo_row
        data = self.provider.request_data(first, last + 1)

        cell_count = len(self.body.contexts)
        for i in range(len(self.rows)):
            row_el = self.rows[i]
            data_row = row_el.lbo_row
            idx = data_row - first
            if idx >= 0 and idx < len(data):
                self.render_context.row = data_row
                self.render_context.value = data[idx]
                self.body.render_content(row_el, data_row)
                self.row_heights[data_row] = (
                    row_el.getBoundingClientRect().height)

                # remove placeholder styling (real data arrived)
                el = row_el
                for j in range(cell_count):
                    if not el:
                        break
                    el.classList.remove("placeholder")
                    el = el.nextElementSibling

        self._update_columns_debounced()
        if self.is_virtual():
            self._apply_anchor_offset()
        self.updated += 1

    def update_anchor(self):
        """Find the first visible row and set anchor.row to it."""
        if not len(self.rows):
            return

        rect = self.element.getBoundingClientRect()
        visible_top = rect.top + self.header.height

        for row_el in self.rows:
            row_rect = row_el.getBoundingClientRect()
            if row_rect.bottom > visible_top:
                self.anchor.row = row_el.lbo_row
                return

        # fallback: use first row
        self.anchor.row = self.rows[0].lbo_row

    def render_value(self, element, name, value):
        # Cache painters per (column name, value type) so a column whose type
        # changes between rows does not reuse the previous-type painter.
        key = f"{name}|{type(value).__name__}"
        painter = self.value_painters[key]
        if painter:
            painter(element, value)
            return

        try:
            painter = adapter.get(type(value), HTML)(None, self.element)
        except Exception as e:
            console.log("no converter for", value,
                        type(value).__name__, repr(e))
            painter = adapter.get(str, HTML)(None, self.element)
        self.value_painters[key] = painter
        painter(element, value)

    def render_header(self, element):
        """can be used to change the element"""
        # called by HeaderTemplate
        pass

    def render_body(self, element):
        """can be used to change the element"""
        # called by RowTemplate
        pass

    def render_footer(self, element):
        """can be used to change the element"""
        # called by FooterTemplate
        pass

    def start_provider(self):
        """Locate / instantiate the data provider. The provider is responsible
        for calling table.set_row_count, which triggers the first render."""
        value = self.context.value
        style = self.context.get("style")
        if isinstance(value, TableDataProvider):
            value.set_table(self)
        else:
            adapter.get(type(value), TableDataProvider, style).set_table(self)

    def unlink(self):
        if self._scroll_tooltip_timer:
            window.clearTimeout(self._scroll_tooltip_timer)
            self._scroll_tooltip_timer = None
        if self.scroll_tooltip_control is not None:
            self.scroll_tooltip_control.unlink()
            self.scroll_tooltip_control = None
        if self._resize_observer is not None:
            self._resize_observer.disconnect()
            self._resize_observer = None
        if self._on_scroll_listener is not None and self.scrollbar_container:
            self.scrollbar_container.removeEventListener(
                "scroll", self._on_scroll_listener)
            self._on_scroll_listener = None
        if self._on_wheel_listener is not None and self.element:
            self.element.removeEventListener(
                "wheel", self._on_wheel_listener)
            self._on_wheel_listener = None
        super().unlink()

    def get_state(self):
        """the table's state"""
        return {"anchor": self.anchor}  # __:jsiter

    def set_state(self, state):
        anchor = (state and state.anchor) or self.anchor
        row = anchor.row if anchor.row is not None else 0
        # clamp defensively - if state arrives before row_count is known,
        # row_count is 0 and any positive row is out of range; set_row_count
        # will re-clamp once the count becomes available.
        if self.row_count and row > self.row_count - 1:
            row = max(0, self.row_count - 1)
        self.anchor.row = row
        self.anchor.bottom = anchor.bottom
