# import larch.lib.adapter as adapter
from larch.bo.client.command import command, CommandHandler
from larch.bo.client.browser import start_main
# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.server import run
from pathlib import Path

location = window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass


if __name__ == "__main__":
    config_logging("hello.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": False,
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")


HTML = """
<div>
<h3>Demonstration of Command Handling</h3>
<p>Press on of the following keys</p>
<ul>
<li><span class="lbo-keystroke">ctrl+k</span><span class="lbo-keystroke">ctrl+i</span>
</ul>
</div>
"""


class Input(CommandHandler):
    def __init__(self, test):
        self.test = test

    def render(self, parent):
        self.element = document.createElement("input")
        self.element.placeholder = "focus me and press ctrl+k ctrl+d"
        self.element.style.width = "20em"
        self.collect_commands(self.element)
        parent.appendChild(self.element)
        return self

    @command(key="ctrl+k ctrl+d,ctrl+f1")
    def default(self):
        self.element.value = "default"

    @command(id_="menu1", global_=True, key="ctrl+k ctrl+m 1")
    def menu(self):
        self.test.output.innerText += "Input menu1 called\n"


class Input2(Input):
    @command(id_="menu2", global_=True, key="ctrl+k ctrl+m 2")
    def menu(self):
        self.test.output.innerText += "Input menu2 called\n"


class CommandTest(CommandHandler):
    def render(self, parent):
        el = document.createElement("div")
        el.innerHTML = HTML
        self.collect_commands(el)
        parent.appendChild(el)
        self.input1 = Input(self).render(el)
        self.input2 = Input2(self).render(el)
        self.output = document.createElement("div")
        el.appendChild(self.output)
        return self

    @command(global_=True, key="ctrl+k ctrl+i")
    def show_menu(self):
        self.output.innerText += "show_menu called\n"


def main():
    window.command_test = CommandTest().render(document.body)


start_main(main)
