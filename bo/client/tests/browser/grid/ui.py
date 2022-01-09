from datetime import date
from larch.reactive import Reactive, Cell, rule
from larch.bo.client.wc.vaadin import vbutton, vinput, vcheckbox, vswitch, styles
from larch.bo.client.grid import Grid
from larch.bo.client.browser import start_main
from larch.bo.client.session import Session
from larch.bo.client.control import register

# __pragma__("skip")
window = document = console = styles
def require(path): pass
def __pragma__(*args): pass
# __pragma__("noskip")


vbutton.register()
vinput.register()
vcheckbox.register()
vswitch.register()


class Model(Reactive):
    first = Cell("Jon")
    last = Cell("Doe")
    email = Cell("jon@doe.com")
    birthday = Cell(date(1985, 10, 1))
    password = Cell("")
    accept = Cell(False)


class AllLive:
    def modify_controls(self):
        super().modify_controls()
        self.control("first").live()
        self.control("last").live()
        self.control("email").live()
        self.control("password").live()


@register(Model)
class CheckForm(AllLive, Grid):
    layout = """
First Name|[first]
Last Name |[last]
Email     |[email]
Birthday  |[birthday]
Password  |[password]@password
          |[accept]
          |<1>
"""

    layout = """
First Name|[first]
Last Name |[last]
Email     |[email]
Password  |[password]@password
          |[accept]
          |<1>
"""

    def modify_controls(self):
        super().modify_controls()
        self.celement("accept").label = "Accept"


@register(Model, "switch")
class SwitchForm(AllLive, Grid):
    layout = """
[first]
[last]
[email]
[password]
Accept|[accept]@switch
      |<1>
"""

    def modify_controls(self):
        super().modify_controls()
        self.set_input("first", "First Name")
        self.set_input("last", "Last Name")
        self.celement("email").label = "Email"
        self.celement("password").label = "Password"
        self.celement("accept")

    def set_input(self, name, label):
        el = self.celement(name)
        el.label = label
        el.style.width = "100%"


class Controller(Grid):
    layout = """
Show Form1     |[.show_form1]@switch
Show Form2     |[.show_form2]@switch
Toggle Birthday|[.birthday_as_text]@switch
Disable        |[.disabled]@switch
Readonly       |[.readonly]@switch
"""

    show_form1 = Cell(True)
    show_form2 = Cell(True)
    birthday_as_text = Cell(False)
    disabled = Cell(False)
    readonly = Cell(False)


class HTMLEditor(Grid):
    layout = """
[.content]@multi|[.content]@html
<1>             |<1>
"""
    content = Cell("")


class Frame(Grid):
    layout = """
f1:[.person]{1}@check |[.controller]{3}
f2:[.person]{2}@switch|   "
[.html]{4}                              |<1>
<1>                   |
"""

    def __init__(self, cv):
        super().__init__(cv)
        self.person = Model()
        self.html = HTMLEditor()
        self.controller = Controller()

    @rule
    def _rule_controller_styles(self):
        if self.element:
            controller = self.control("controller")
            self.container("f1").style.display = "" if controller.show_form1 else "none"
            self.container("f2").style.display = "" if controller.show_form2 else "none"

            console.log("***set disabled?", controller.disabled)
            self.contexts["f1"].set("disabled", controller.disabled)
            self.contexts["f2"].set("disabled", controller.disabled)
            self.contexts["f1"].set("readonly", controller.readonly)
            self.contexts["f2"].set("readonly", controller.readonly)


def main():
    print("start main")
    Session(Frame()).boot()


start_main(main)
