from datetime import date
from larch.reactive import Reactive, Cell, rule
from larch.bo.client.wc.vaadin import vbutton, vinput, vcheckbox, vswitch, vdate, styles
from larch.bo.client.grid import Grid
from larch.bo.client.browser import start_main
from larch.bo.client.session import Session
from larch.bo.client.control import register
from larch.bo.client.command import label, icon
from larch.bo.client.animate import animate

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
Email     |[email]@email
Birthday  |[birthday]
Password  |[password]@password
Accept    |[accept]
          |[.open]
          |<1>
"""

    @icon("check")
    @label("Open Dialog")
    def open(self):
        console.log("submit")


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

    def set_input(self, name, label):
        el = self.celement(name)
        el.label = label
        el.style.width = "100%"


class Controller(Grid):
    layout = """
Show Form1     |[.show_form1]@switch
Show Form2     |[.show_form2]@switch
Toggle Acccept |[.accept_is_switch]@switch
Disable        |[.disabled]@switch
Readonly       |[.readonly]@switch
"""

    show_form1 = Cell(True)
    show_form2 = Cell(True)
    accept_is_switch = Cell(False)
    disabled = Cell(False)
    readonly = Cell(False)


class HTMLEditor(Grid):
    layout = """
Editor               |Preview
edit:[.content]@multi|preview:[.content]@html|<1>
<1>                  |<1>
"""
    content = Cell("""
<h1>Hello</h1>
World""")

    def modify_controls(self):
        edit = self.control("edit")
        style = edit.element.style
        style.width = "100%"
        style.height = "100%"
        edit.live()


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
    def _rule_accept_styles(self):
        if self.element:
            controller = self.control("controller")
            self.control("f1").contexts["accept"].set(
                "style", "switch" if controller.accept_is_switch else "")

    @rule
    def _rule_controller_styles(self):
        if self.element:
            controller = self.control("controller")
            animate.show(self.container("f1"), controller.show_form1)
            animate.show(self.container("f2"), controller.show_form2)

            self.contexts["f1"].set("disabled", controller.disabled)
            self.contexts["f2"].set("disabled", controller.disabled)
            self.contexts["f1"].set("readonly", controller.readonly)
            self.contexts["f2"].set("readonly", controller.readonly)


def main():
    print("start main")
    Session(Frame()).boot()


start_main(main)
