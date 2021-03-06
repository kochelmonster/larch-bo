from larch.reactive import Cell, rule
from ..command import command

# __pragma__("skip")
window = None
# __pragma__ ("noskip")


class MixinCursor:
    """A cursor mixin for Table, must be combined with MixinCommandHandler"""
    cursor = Cell(0)
    old_cursor = 0

    def render(self, parent):
        super().render(parent)
        self.set_css_selection_class()

    def set_css_selection_class(self):
        self.element.classList.add("single-selection")

    @command(key="up")
    def cursor_up(self):
        self.set_cursor(self.cursor-1)

    @command(key="down")
    def cursor_down(self):
        self.set_cursor(self.cursor+1)

    @command(key="home")
    def cursor_home(self):
        self.set_cursor(0)

    @command(key="end")
    def cursor_end(self):
        self.set_cursor(self.row_count-1)

    @command(key="pageup")
    def cursor_pageup(self):
        cursor = self.get_pageup_position()
        if cursor is not None:
            self.set_cursor(cursor)

    @command(key="pagedown")
    def cursor_pagedown(self):
        cursor = self.get_pagedown_position()
        if cursor is not None:
            self.set_cursor(cursor, True)

    @command(key="pointerdown-0")
    def cursor_mouse(self):
        event = window.lbo.command_context.event
        for p in event.composedPath():
            if p.classList and p.classList.contains("selector"):
                return

        row = self.row_from_event(event)
        if row >= 0:
            self.set_cursor(row)
        self.element.focus()
        return False

    def row_from_event(self, event):
        for element in event.composedPath():
            row = element.lbo_row
            if row or row == 0:
                return row
        return -4

    def get_pageup_position(self):
        height = self.element.clientHeight - self.header.height - self.footer.height
        return max(int(self.cursor - height/self.current_row_height), 0)

    def get_pagedown_position(self):
        height = self.element.clientHeight - self.header.height - self.footer.height
        return min(int(self.cursor + height/self.current_row_height), self.row_count - 1)

    def set_cursor(self, cursor, bottom=False):
        cursor = min(max(cursor, 0), self.row_count-1)
        self.cursor = cursor
        self.scroll_to_cursor(bottom)
        return cursor

    def get_event_context(self):
        row = name = None
        col = -1
        event = window.lbo.command_context.event
        if event and event.target:
            row = event.target.lbo_row
            if not row and row != 0:
                row = None
            else:
                col = event.target.lbo_col

        if row is None:
            row = self.cursor

        if col >= 0:
            if row == -1:
                section = self.header
            elif row == -2:
                section = self.footer
            else:
                section = self.body
            name = section.contexts[col+1]["name"]
        return {"row": row, "col": col, "name": name}  # __:jsiter

    def get_tab_elements(self):
        return [self.element]

    def scroll_to_cursor(self, bottom=False):
        start = self.rows[0].lbo_row
        row = self.rows[self.cursor-start]
        if row:
            # scrollIntoView does not work with sticky headers/footers
            rect = self.element.getBoundingClientRect()
            min_top = rect.top + self.header.height
            max_bottom = rect.bottom - self.footer.height

            rect = row.getBoundingClientRect()
            if rect.bottom > max_bottom:
                self.element.scrollBy(0, rect.bottom-max_bottom+1)
                rect = row.getBoundingClientRect()

            if rect.top < min_top:
                self.element.scrollBy(0, rect.top-min_top)

            self.update_anchor()
            self.updated += 1
        else:
            # outside the display block
            self.anchor.row = self.cursor
            if bottom:
                self.anchor.offset = max_bottom-min_top-1
                self.update_display()
                self.scroll_to_cursor()
            else:
                self.anchor.offset = 0
                self.update_display()

    def get_state(self):
        state = super().get_state()
        state["cursor"] = self.cursor
        return state

    def set_state(self, state):
        super().set_state(state)
        self.cursor = (state and state.cursor) or self.cursor

    def set_row_count(self, count):
        self.cursor = min(self.cursor, count-1)
        super().set_row_count(count)

    @rule
    def _rule_update_cursor(self):
        if self.updated:
            cursor = self.cursor
            yield
            for el in self.element.querySelectorAll(".cursor"):
                el.classList.remove("cursor")

            if not self.rows.length:
                return

            self.old_cursor = cursor
            start = self.rows[0].lbo_row
            row = self.rows[cursor-start]
            if row:
                for c in self.body.contexts:
                    row.classList.add("cursor")
                    row = row.nextElementSibling
