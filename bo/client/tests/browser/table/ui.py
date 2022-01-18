from larch.reactive import Cell
from larch.bo.client.wc.vaadin import vbutton, vinput, vcheckbox, vswitch, vdate, styles
from larch.bo.client.grid import Grid
from larch.bo.client.table import Table, TableDataProvider
from larch.bo.client.browser import start_main, PyPromise
from larch.bo.client.session import Session
from larch.bo.client.control import register

# __pragma__("skip")
window = document = console = styles
def require(path): pass
def __pragma__(*args): pass
# __pragma__("noskip")


vdate.register()
vbutton.register()
vinput.register()
vcheckbox.register()
vswitch.register()


class Controller(Grid):
    layout = """
Disable |[.disabled]@switch
Readonly|[.readonly]@switch
"""

    disabled = Cell(False)
    readonly = Cell(False)


class EmployeeLoader(TableDataProvider):
    def __repr__(self):
        return "<EmployeeLoader>"

    def ready(self):
        def loaded(value):
            self.data = value
            promise.resolve()

        promise = PyPromise()
        window.lbo.server.load_data(0, 10000).then(loaded)
        return promise

    def get_data(self):

        del self.get_data
        self.get_data = lambda x=None: self.data
        return self.data

    def get_visible_count(self):
        return len(self.data)

    def get_item(self, row):
        return self.data[row]

    def avg_age(self):
        data = self.data
        return sum(d.age for d in data) / len(data)


@register(EmployeeLoader)
class Employees(Table):
    layout = """
    Emplyoees{c}
Name      | Office     |Age          |Start
---
[.js.name]|[.js.office]|[.js.age]{r} |[.js.start]
---
                       |[.avg_age]{r}|
    Average Age{c}
"""

    @property
    def avg_age(self):
        return self.provider.avg_age()


class Frame(Grid):
    layout = """
      (0,4em)
[.employees]|[.controller]|<1>
      (0,4.1em)
"""

    def __init__(self, cv):
        super().__init__(cv)
        self.employees = EmployeeLoader()
        self.controller = Controller()

    def modify_controls(self):
        self.container("employees").classList.add("scrollable")


def main():
    print("start main")
    Session(Frame()).boot()


start_main(main)
