# import larch.lib.adapter as adapter
import larch.bo.client.polymer
from larch.bo.client.grid import Grid
from larch.bo.client.control import ControlContext, Control, register
from larch.reactive import Cell, rule
from larch.bo.client.browser import create_element

# __pragma__("skip")
import sys
from larch.lib.test import config_logging
from larch.bo.server import run
from pathlib import Path

larch.bo.client.polymer
window = document = None


if __name__ == "__main__":
    config_logging("grid.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": True,
    }
    sys.exit(run(__file__, config=config))
# __pragma__ ("noskip")


class TestGrid(Grid):
    layout = """
lvalue:Value{r}|[.value]{l}
               |[.submit]
bottom:this is some button test{cb}|<1>
    <1>        |<1>
"""

    value = Cell("Test")

    def prepare_contexts(self):
        print("create contexts")
        self.contexts["value"]["no_label_float"] = True   # __: opov

    def submit(self):
        print("submit")

    @rule
    def _rule_value_changed(self):
        print("changed value", self.value)


def func(): pass


@register(type(func))
class ButtonControl(Control):
    def render(self, parent):
        self.button = create_element("button")
        self.button.innerText = self.context["name"] or "Press"   # __: opov
        parent.appendChild(self.button)
        self.button.addEventListener("click", self.on_click)

    def on_click(self, event):
        print("click", event)
        self.context.value()


def main():
    grid = TestGrid()
    grid.context["style"] = "polymer"  # __: opov
    print("grid", grid.cells)
    grid.render(document.querySelector("body"))
    print("functype", type(grid.submit).__name__)

    c = ControlContext(10)
    print("1. value", c.value)
    c.value = 20
    print("2. value", c.value)
    print("parent", c.parent)
    c["test"] = 10
    print("test", c["test"])
    window.grid = grid


document.addEventListener('DOMContentLoaded', main)
