from larch.bo.client.control import Control, register as cregister
from larch.bo.client.browser import loading_modules

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@vaadin/button")
document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import("@vaadin/button");
})());
''')


class ButtonControl(Control):
    TAG = "vaadin-button"

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)

        label = self.context.value.__label__
        if not label and self.context.value.__org__:
            label = self.context.value.__org__.__label__
        if not label:
            label = self.context["name"]   # __: opov

        self.element.innerText = label
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
