"""components for table"""
from ...table import Table
from . import vcheckbox   # import the vaadin components

# __pragma__("skip")
console = document = vcheckbox
def __pragma__(*args): pass
# __pragma__("noskip")


class TableCheckbox:
    TAG = "vaadin-checkbox"

    def __init__(self, grid):
        self.grid = grid

    def create_template(self, parent):
        box = document.createElement(self.TAG)
        parent.appendChild(box)
        parent.classList.add("selector")

    def render(self, parent):
        parent.firstChild.addEventListener("change", self.on_change)
        parent.firstChild.checked = self.grid.is_selected(parent.lbo_row)
        parent.update_selector = self.update_selector

    def update_selector(self, parent):
        if parent.lbo_row >= 0:
            parent.firstChild.checked = self.grid.is_selected(parent.lbo_row)
        else:
            range_ = self.grid.selection.range
            single = self.grid.selection.single
            if not bool(single):
                if range_[0] == 0 and range_[1] == self.grid.row_count - 1:
                    parent.firstChild.checked = True
                    parent.firstChild.indeterminate = False
                    return

                if not range_.length or range_[0] == range_[1]:
                    parent.firstChild.checked = False
                    parent.firstChild.indeterminate = False
                    return

            parent.firstChild.indeterminate = True

    def on_change(self, event):
        row = self.grid.row_from_event(event)
        if row >= 0:
            self.grid.set_cursor(row, False, True)
        else:
            if event.target.checked:
                self.grid.select_all()
            else:
                self.grid.selection = self.grid.clear_selection(self.grid.cursor)
            self.grid.display_selection()


def register():
    # __pragma__("jsiter")
    Table.control_handlers = {
        "checkbox": TableCheckbox
    }
    # __pragma__("nojsiter")
