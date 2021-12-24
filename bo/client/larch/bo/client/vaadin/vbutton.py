from larch.bo.client.control import Control, register as cregister

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.extend(["@vaadin/button"])
document = None
def require(p): pass
# __pragma__("noskip")


require('@vaadin/button')


class ButtonControl(Control):
    TAG = "vaadin-button"

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)
        self.element.innerText = self.context["name"]   # __: opov
        self.element.addEventListener("click", self.on_click)

    def on_click(self, event):
        self.context.value()

    def unlink(self):
        super().unlink()
        self.element = None

    def get_tab_elements(self):
        return [self.element]


def register(style=""):
    cregister(type(cregister), style)(ButtonControl)
