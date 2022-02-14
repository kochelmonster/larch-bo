from larch.reactive import Cell
from ..command import command
from .cursor import MixinCursor

# __pragma__("skip")
window = JSON = None
# __pragma__ ("noskip")


NULL_SELECTION = {"range": [], "single": {}, "anchor": 0}  # __:jsiter


class MixinSelection(MixinCursor):
    """A multiple selection mixin for Table, must be combined with MixinCommandHandler"""
    selection = Cell(NULL_SELECTION)

    def set_css_selection_class(self):
        self.element.classList.add("multi-selection")

    def is_selected(self, row):
        if (self.selection.range[0] <= row <= self.selection.range[1]
                and self.selection.single[row] is not False):
            return True
        return self.selection.single[row] is True

    @command(key="shift+up")
    def selection_up(self):
        self.set_cursor(self.cursor-1, True)

    @command(key="shift+down")
    def selection_down(self):
        self.set_cursor(self.cursor+1, True)

    @command(key="shift-pageup")
    def selection_pageup(self):
        cursor = self.get_pageup_position()
        if cursor is not None:
            self.set_cursor(cursor, True)

    @command(key="shift-pagedown")
    def selection_pagedown(self):
        cursor = self.get_pagedown_position()
        if cursor is not None:
            self.set_cursor(cursor, True)

    @command(key="shift+home")
    def selection_home(self):
        self.set_cursor(0, True)

    @command(key="shift+end")
    def selection_end(self):
        self.set_cursor(self.row_count - 1, True)

    @command(key="ctrl+up")
    def marker_up(self):
        super().set_cursor(self.cursor-1)

    @command(key="ctrl+down")
    def marker_down(self):
        super().set_cursor(self.cursor+1)

    @command(key="ctrl+space")
    def set_marker(self):
        self.set_cursor(self.cursor, False, True)

    @command(key="shift+pointerdown-0")
    def click_select(self):
        self.element.focus()
        row = self.row_from_event(window.lbo.command_context.event)
        if row >= 0:
            self.set_cursor(row, True)

    @command(key="ctrl+pointerdown-0")
    def click_mark(self):
        self.element.focus()
        row = self.row_from_event(window.lbo.command_context.event)
        if row >= 0:
            self.set_cursor(row, False, True)

    @command(key="ctrl+a")
    def select_all(self):
        # __pragma__("jsiter")
        self.selection = {
            "anchor": self.selection.anchor,
            "range": [0, self.row_count-1],
            "single": {}
        }
        self.display_selection()
        # __pragma__("nojsiter")

    def range_select(self, row):
        row = min(max(row, 0), self.row_count-1)
        range_ = [self.selection.anchor, row]
        if range_[0] > range_[1]:
            range_ = [range_[1], range_[0]]

        # __pragma__("jsiter")
        return {
            "anchor": self.selection.anchor,
            "range": range_,
            "single": self.selection.single
        }
        # __pragma__("nojsiter")

    def single_select(self, row):
        range_ = self.selection.range
        single = JSON.parse(JSON.stringify(self.selection.single))

        if row + 1 == range_[0]:
            range_ = [row, range_[1]]

        elif row - 1 == range_[1]:
            range_ = [range_[0], row]

        elif range_[0] == row:
            range_ = [row+1, range_[1]]

        elif range_[1] == row:
            range_ = [range_[0], row-1]

        elif range_[0] < row < range_[1]:
            if single[row] is False:
                del single[row]
            else:
                single[row] = False
        else:
            if single[row] is True:
                del single[row]
            else:
                single[row] = True

        if range_[0] > range_[1]:
            range_ = []

        # __pragma__("jsiter")
        return {
            "anchor": self.selection.anchor,
            "range": range_,
            "single": single
        }
        # __pragma__("nojsiter")

    def clear_selection(self, cursor):
        # __pragma__("jsiter")
        return {
            "anchor": cursor,
            "range": [cursor, cursor],
            "single": {}
        }
        # __pragma__("nojsiter")

    def render_body(self, element):
        if self.is_selected(element.lbo_row):
            element.classList.add("selection")
        else:
            element.classList.remove("selection")

    def set_cursor(self, cursor, range_select=False, single_select=False):
        if range_select:
            selection = self.range_select(cursor)
        elif single_select:
            selection = self.single_select(cursor)
        else:
            selection = self.clear_selection(cursor)

        self.selection = selection
        self.display_selection()

        super().set_cursor(cursor)

    def display_selection(self):
        for row in self.viewport.querySelectorAll("section"):
            if self.is_selected(row.lbo_row):
                row.classList.add("selection")
            else:
                row.classList.remove("selection")

        for el in self.viewport.querySelectorAll(".selector"):
            el.update_selector(el)

        self.updated += 1

    def get_state(self):
        state = super().get_state()
        state["selection"] = self.selection
        return state

    def set_state(self, state):
        super().set_state(state)
        self.selection = state.selection or self.selection


class MixinToggleSelector:
    """A mixin that toggles selector visibility with long clicks"""

    def render_frame(self):
        self.element.classList.add("hide-selector")
        super().render_frame()

    @command(key="longclick-0")
    def toggle_selector(self):
        if self.element.classList.contains("hide-selector"):
            self.element.classList.remove("hide-selector")
        else:
            self.element.classList.add("hide-selector")
        self.reset_widths()
