from larch.reactive import Cell, rule, Reactive
from larch.bo.client.wc.vaadin import vbutton, vinput, vcheckbox, vswitch, vdate, styles, table
from larch.bo.client.grid import Grid
from larch.bo.client.i18n import create_number_painter
from larch.bo.client.table import Table, provider, cursor, selection, state
from larch.bo.client.command import MixinCommandHandler, command
from larch.bo.client.browser import start_main
from larch.bo.client.session import Session
from larch.bo.client.control import register


# __pragma__("skip")
class Console:
    def log(self, *args):
        pass


window = document = styles
console = Console()
def require(path): pass
def __pragma__(*args): pass
# __pragma__("noskip")


# __pragma__("ecom")
vdate.register()
vbutton.register()
vinput.register()
vcheckbox.register()
vswitch.register()
table.register()


class Controller(Grid):
    layout = """
Disable      |[.disabled]@switch
Readonly     |[.readonly]@switch
Count        |[.count]
Toggle Loader|[.chunked]@switch
"""

    disabled = Cell(False)
    readonly = Cell(False)
    count = Cell(500)
    chunked = Cell(False)

    @rule
    def _rule_change_count(self):
        if self.element:
            self.contexts["count"].set("disabled", self.chunked)


class EmployeeLoader(provider.DelayedDataProvider, Reactive):
    """?
    # __pragma__("jsiter")
    PLACEHOLDER = {
        '__placeholder__': True,
        'id_': 10000,
        'name': 'Jennifer Davis',
        'office': 'Chaneystad',
        'age': 162, 'salary': 7295.72,
        'start': __new__(Date(2020, 3, 20)),
        'address': '45243 Cassandra Passage Suite 025\nSouth Allisonberg, RI 03664'
    }
    # __pragma__("nojsiter")
    ?"""

    count = 1000
    table = None
    avg_age = Cell(0)
    avg_salary = Cell(0)

    def __repr__(self):
        return "<EmployeeLoader>"

    def set_table(self, table):
        self.table = table
        self.table.provider = self
        self.resolve_data()

    def load_data(self):
        return window.lbo.server.load_data(0, self.count)

    def set_count(self, count):
        console.log("***set count", count)
        self.count = count
        if self.table:
            self.set_data(None)
            self.table.clear()
            self.resolve_data()

    def set_data(self, data):
        super().set_data(data)
        if data:
            self.avg_age = sum([data[i].age for i in range(len(data))]) / len(data)
            self.avg_salary = sum([data[i].salary for i in range(len(data))]) / len(data)
        else:
            self.avg_age = self.avg_salary = 0


class ChunkedEmployeeLoader(provider.DelayedChunkProvider):
    """?
    PLACEHOLDER = EmployeeLoader.PLACEHOLDER
    ?"""

    def load_chunk(self, row):
        return window.lbo.server.load_chunk(row)


@register(EmployeeLoader)
class Employees(state.MixinState, cursor.MixinCursor, MixinCommandHandler, Table):
    layout = """
    Emplyoees{c}
Id       |Name      | Office     |Age          |Start      |Salary           |Address
---
[.js.id_]|[.js.name]|[.js.office]|[.js.age]{r} |[.js.start]|[.js.salary]{r}  |[.js.address]
---
[.msg]                           |[.avg_age]{r}|           |[.avg_salary]{r} |
    Average Age{c}
"""

    msg = Cell("Hello")

    def __init__(self, cv=None):
        super().__init__(cv)

        # __pragma__("jsiter")
        style = {
            "currency": "EUR",
            "currencyDisplay": "symbol",
            "style": "currency"
        }
        # __pragma__("nojsiter")
        self.value_painters["salary"] = sp = create_number_painter(style)
        self.value_painters["avg_salary"] = sp

    """
    def process_layout(self):
        # example for frozen columns
        super().process_layout()
        col0 = self.body.template.content.children[1]
        col0.style.left = 0
        col0.classList.add("frozen")
        col0.style.background = "hsl(213deg 100% 95%)"
        col0.style.borderRight = "1px solid black"
    """

    @property
    def avg_age(self):
        return self.provider.avg_age

    @property
    def avg_salary(self):
        return self.provider.avg_salary

    @command(key="return,dblclick-0")
    def open(self):
        context = self.get_event_context()
        console.log("***open", context)


@register(ChunkedEmployeeLoader)
class ChunkedEmployees(state.MixinState, selection.MixinToggleSelector,
                       selection.MixinSelection, MixinCommandHandler, Table):
    layout = """
    Emplyoees{c}
*    |Id       |Name      | Office     |Age         |Start      |Salary         |Address
---
*{rt}|[.js.id_]|[.js.name]|[.js.office]|[.js.age]{r}|[.js.start]|[.js.salary]{r}|[.js.address]
                                                                                |<1>
"""

    def __init__(self, cv=None):
        super().__init__(cv)

        # __pragma__("jsiter")
        style = {
            "currency": "EUR",
            "currencyDisplay": "symbol",
            "style": "currency"
        }
        # __pragma__("nojsiter")
        self.value_painters["salary"] = create_number_painter(style)

    @command(key="return,dblclick-0")
    def open(self):
        context = self.get_event_context()
        console.log("***open", context)


class Frame(Grid):
    employees = Cell()

    layout = """
      (0,4em)
[.employees]{l}|[.controller]|<1>
      (0,4.1em)
<1>            |
"""

    def __init__(self, cv):
        super().__init__(cv)
        self.employees = EmployeeLoader()
        self.controller = Controller()

    @rule
    def _rule_change_count(self):
        count = self.controller.count
        yield
        self.employees.set_count(count)

    @rule
    def _rule_toggle_employees(self):
        chunked = self.controller.chunked
        yield
        if chunked:
            self.employees = ChunkedEmployeeLoader()
        else:
            self.employees = EmployeeLoader()
            self.employees.set_count(self.controller.count)


def main():
    print("start main")
    document.body.style.userSelect = "none"
    Session(Frame()).boot()


start_main(main)
