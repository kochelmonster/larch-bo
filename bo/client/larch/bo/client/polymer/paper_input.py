from larch.reactive import rule, Cell
from larch.bo.client.control import Control, register

# __pragma__("skip")
from larch.bo.packer import parcel
document = None
parcel.NEEDED_PACKAGES.add("@polymer/paper-input")
def require(p): pass
# __pragma__("noskip")


require("@polymer/paper-input/paper-input.js")


@register(type(""), "polymer")
class PaperInput(Control):
    element = Cell()

    def render(self, parent):
        self.element = document.createElement("paper-input")
        parent.appendChild(self.element)
        self.element.addEventListener("change", self.on_change)

    def on_change(self, event):
        self.context.value = self.element.value

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.setAttribute("value", self.context.value)
