from larch.reactive import Cell, rule
from larch.bo.client.wc.vaadin import vbutton, vinput, vcheckbox, vswitch, vdate, styles
from larch.bo.client.grid import Grid
from larch.bo.client.i18n import create_number_painter
from larch.bo.client.table import Table, provider, cursor
from larch.bo.client.command import MixinCommandHandler, command
from larch.bo.client.browser import start_main
from larch.bo.client.session import Session
from larch.bo.client.control import register

# __pragma__("skip")
window = document = console = styles
def require(path): pass
def __pragma__(*args): pass
# __pragma__("noskip")


# __pragma__("ecom")
vdate.register()
vbutton.register()
vinput.register()
vcheckbox.register()
vswitch.register()


class Controller(Grid):
    layout = """
Disable |[.disabled]@switch
Readonly|[.readonly]@switch
Count   |[.count]
"""

    disabled = Cell(False)
    readonly = Cell(False)
    count = Cell(500)


class EmployeeLoader(provider.DelayedDataProvider):
    """?
    # __pragma__("jsiter")
    placeholder = {
        'id_': 10000,
        'name': 'Jennifer Davis',
        'office': 'Chaneystad',
        'age': 62, 'salary': 7295.72,
        'start': __new__(Date(2020, 3, 20)),
        'address': '45243 Cassandra Passage Suite 025\nSouth Allisonberg, RI 03664'
    }
    # __pragma__("nojsiter")
    ?"""

    count = 1000
    table = None

    def __repr__(self):
        return "<EmployeeLoader>"

    def set_table(self, table):
        self.table = table
        self.resolve_data()
        return self

    def load_data(self):
        return window.lbo.server.load_data(0, self.count)

    def set_count(self, count):
        console.log("***set count", count)
        self.count = count
        if self.table:
            self.set_data(None)
            self.resolve_data()

    def avg_age(self):
        data = self.get_data()
        return sum([data[i].age for i in range(len(data))]) / len(data) if data else 0

    def avg_salary(self):
        data = self.get_data()
        return sum([data[i].salary for i in range(len(data))]) / len(data) if data else 0


@register(EmployeeLoader)
class Employees(cursor.MixinCursor, MixinCommandHandler, Table):
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
        return self.provider.avg_age()

    @property
    def avg_salary(self):
        return self.provider.avg_salary()

    @command(key="return,dblclick-0")
    def open(self):
        context = self.get_event_context()
        console.log("***open", context)


class Frame(Grid):
    layout = """
      (0,4em)
[.employees]{e}|[.controller]|<1>
      (0,4.1em)
"""

    def __init__(self, cv):
        super().__init__(cv)
        self.employees = window.emps = EmployeeLoader()
        self.controller = Controller()

    @rule
    def _rule_change_count(self):
        count = self.controller.count
        yield
        self.employees.set_count(count)


def main():
    print("start main")
    Session(Frame()).boot()


start_main(main)
