from larch.reactive import rule, Cell
from larch.bo.client.control import Control, register as cregister

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.extend([
    "@vaadin/number-field", "@vaadin/integer-field", "@vaadin/text-field"])
document = None
def require(p): pass
# __pragma__("noskip")


require('@vaadin/text-field')
require("@vaadin/number-field")
require("@vaadin/integer-field")


class TextControl(Control):
    TAG = "vaadin-text-field"
    element = Cell()

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)
        self.element.addEventListener("change", self.on_change)

    def unlink(self):
        super().unlink()
        self.element = None

    def get_tab_elements(self):
        return [self.element]

    def on_change(self, event):
        self.context.value = self.element.value

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.setAttribute("value", self.context.value)


class IntControl(TextControl):
    TAG = "vaadin-number-field"


class FloatControl(TextControl):
    TAG = "vaadin-number-field"


def register(style=""):
    cregister(type(""), style)(TextControl)
    cregister(type(2), style)(IntControl)
    cregister(type(2.1), style)(FloatControl)
